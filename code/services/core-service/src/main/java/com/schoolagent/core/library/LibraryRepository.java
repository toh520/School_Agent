package com.schoolagent.core.library;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.schoolagent.core.library.LibraryDtos.BookResponse;
import com.schoolagent.core.library.LibraryDtos.LibraryBookUpsertRequest;
import com.schoolagent.core.library.LibraryDtos.LoanResponse;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** JDBC access for the single-library catalog and its inventory-backed loans. */
@Repository
class LibraryRepository {
  private static final TypeReference<LinkedHashMap<String, Object>> MAP_TYPE =
      new TypeReference<>() {};
  private final JdbcTemplate jdbc;
  private final ObjectMapper objectMapper;

  LibraryRepository(JdbcTemplate jdbc, ObjectMapper objectMapper) {
    this.jdbc = jdbc;
    this.objectMapper = objectMapper;
  }

  List<BookResponse> books(String query, String category, String tag, Boolean availableOnly) {
    StringBuilder where =
        new StringBuilder(" WHERE book.deleted_at IS NULL AND holding.deleted_at IS NULL");
    List<Object> parameters = new ArrayList<>();
    if (query != null && !query.isBlank()) {
      where.append(
          " AND (book.name ILIKE ? OR book.payload->>'isbn' ILIKE ? OR book.payload->>'publisher' ILIKE ? OR book.payload::text ILIKE ?)");
      String pattern = "%" + query.trim() + "%";
      parameters.add(pattern);
      parameters.add(pattern);
      parameters.add(pattern);
      parameters.add(pattern);
    }
    if (category != null && !category.isBlank()) {
      where.append(" AND book.payload->>'category' = ?");
      parameters.add(category.trim());
    }
    if (tag != null && !tag.isBlank()) {
      where.append(" AND book.payload->'tags' @> to_jsonb(ARRAY[?]::text[])");
      parameters.add(tag.trim());
    }
    if (Boolean.TRUE.equals(availableOnly)) {
      where.append(" AND COALESCE((holding.payload->>'availableCount')::int, 0) > 0");
    }
    return jdbc.query(
        """
        SELECT book.id, book.code, book.name, book.payload AS book_payload,
               holding.id AS holding_id, holding.payload AS holding_payload
        FROM book JOIN library_holding holding ON holding.parent_code = book.code
        """
            + where
            + " ORDER BY book.name LIMIT 300",
        this::mapBook,
        parameters.toArray());
  }

  Optional<BookResponse> book(UUID bookId) {
    return jdbc
        .query(
            """
        SELECT book.id, book.code, book.name, book.payload AS book_payload,
               holding.id AS holding_id, holding.payload AS holding_payload
        FROM book JOIN library_holding holding ON holding.parent_code = book.code
        WHERE book.id = ? AND book.deleted_at IS NULL AND holding.deleted_at IS NULL
        """,
            this::mapBook,
            bookId)
        .stream()
        .findFirst();
  }

  Optional<BookResponse> lockBook(UUID bookId) {
    return jdbc
        .query(
            """
        SELECT book.id, book.code, book.name, book.payload AS book_payload,
               holding.id AS holding_id, holding.payload AS holding_payload
        FROM book JOIN library_holding holding ON holding.parent_code = book.code
        WHERE book.id = ? AND book.deleted_at IS NULL AND holding.deleted_at IS NULL
        FOR UPDATE OF holding
        """,
            this::mapBook,
            bookId)
        .stream()
        .findFirst();
  }

  boolean hasCurrentLoan(UUID userId, UUID bookId) {
    Long count =
        jdbc.queryForObject(
            "SELECT COUNT(*) FROM library_loan WHERE user_id = ? AND book_id = ? AND status = 'BORROWED'",
            Long.class,
            userId,
            bookId);
    return count != null && count > 0;
  }

  UUID createLoan(UUID userId, BookResponse book) {
    UUID id = UUID.randomUUID();
    jdbc.update(
        "INSERT INTO library_loan(id, user_id, book_id, holding_id) VALUES (?, ?, ?, ?)",
        id,
        userId,
        book.id(),
        book.holdingId());
    jdbc.update(
        """
        UPDATE library_holding
        SET payload = jsonb_set(
                jsonb_set(payload, '{availableCount}', to_jsonb(GREATEST((payload->>'availableCount')::int - 1, 0))),
                '{availabilityStatus}',
                to_jsonb(CASE WHEN (payload->>'availableCount')::int - 1 > 0 THEN 'AVAILABLE' ELSE 'UNAVAILABLE' END::text)
            ), updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        book.holdingId());
    return id;
  }

  Optional<LoanResponse> loan(UUID userId, UUID loanId, boolean lock) {
    String suffix = lock ? " FOR UPDATE OF loan" : "";
    return jdbc
        .query(
            """
        SELECT loan.id, loan.book_id, loan.status, loan.borrowed_at, loan.returned_at,
               book.name, book.payload AS book_payload, holding.payload AS holding_payload
        FROM library_loan loan
        JOIN book ON book.id = loan.book_id
        JOIN library_holding holding ON holding.id = loan.holding_id
        WHERE loan.id = ? AND loan.user_id = ?
        """
                + suffix,
            this::mapLoan,
            loanId,
            userId)
        .stream()
        .findFirst();
  }

  List<LoanResponse> loans(UUID userId) {
    return jdbc.query(
        """
        SELECT loan.id, loan.book_id, loan.status, loan.borrowed_at, loan.returned_at,
               book.name, book.payload AS book_payload, holding.payload AS holding_payload
        FROM library_loan loan
        JOIN book ON book.id = loan.book_id
        JOIN library_holding holding ON holding.id = loan.holding_id
        WHERE loan.user_id = ?
        ORDER BY CASE WHEN loan.status = 'BORROWED' THEN 0 ELSE 1 END, loan.borrowed_at DESC
        """,
        this::mapLoan,
        userId);
  }

  void returnLoan(UUID loanId, UUID userId) {
    UUID holdingId =
        jdbc.queryForObject(
            "SELECT holding_id FROM library_loan WHERE id = ? AND user_id = ? FOR UPDATE",
            UUID.class,
            loanId,
            userId);
    jdbc.queryForObject(
        "SELECT id FROM library_holding WHERE id = ? FOR UPDATE", UUID.class, holdingId);
    jdbc.update(
        "UPDATE library_loan SET status = 'RETURNED', returned_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        loanId,
        userId);
    jdbc.update(
        """
        UPDATE library_holding
        SET payload = jsonb_set(
                jsonb_set(payload, '{availableCount}', to_jsonb(LEAST((payload->>'availableCount')::int + 1, (payload->>'totalCount')::int))),
                '{availabilityStatus}', to_jsonb('AVAILABLE'::text)
            ), updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        holdingId);
  }

  BookResponse createCombined(LibraryBookUpsertRequest request, UUID actorId) {
    String code = "BOOK-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    UUID bookId = UUID.randomUUID();
    UUID holdingId = UUID.randomUUID();
    jdbc.update(
        "INSERT INTO book(id, code, name, payload, source, created_by, updated_by) VALUES (?, ?, ?, ?::jsonb, '智慧图书馆管理', ?, ?)",
        bookId,
        code,
        request.name().trim(),
        bookPayload(request),
        actorId,
        actorId);
    jdbc.update(
        "INSERT INTO library_holding(id, code, name, parent_code, payload, source, created_by, updated_by) VALUES (?, ?, ?, ?, ?::jsonb, '智慧图书馆管理', ?, ?)",
        holdingId,
        "HOLD-" + code.substring(5),
        request.name().trim() + "馆藏",
        code,
        holdingPayload(request),
        actorId,
        actorId);
    return book(bookId).orElseThrow();
  }

  BookResponse updateCombined(UUID bookId, LibraryBookUpsertRequest request, UUID actorId) {
    BookResponse current = book(bookId).orElseThrow();
    jdbc.update(
        "UPDATE book SET name = ?, payload = ?::jsonb, updated_by = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        request.name().trim(),
        bookPayload(request),
        actorId,
        bookId);
    jdbc.update(
        "UPDATE library_holding SET name = ?, payload = ?::jsonb, updated_by = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        request.name().trim() + "馆藏",
        holdingPayload(request),
        actorId,
        current.holdingId());
    return book(bookId).orElseThrow();
  }

  boolean hasOutstandingLoans(UUID bookId) {
    Long count =
        jdbc.queryForObject(
            "SELECT COUNT(*) FROM library_loan WHERE book_id = ? AND status = 'BORROWED'",
            Long.class,
            bookId);
    return count != null && count > 0;
  }

  void deactivateCombined(UUID bookId, UUID actorId) {
    BookResponse current = book(bookId).orElseThrow();
    jdbc.update(
        "UPDATE library_holding SET status = 'INACTIVE', deleted_at = CURRENT_TIMESTAMP, updated_by = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        actorId,
        current.holdingId());
    jdbc.update(
        "UPDATE book SET status = 'INACTIVE', deleted_at = CURRENT_TIMESTAMP, updated_by = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        actorId,
        bookId);
  }

  private String bookPayload(LibraryBookUpsertRequest request) {
    Map<String, Object> payload = new LinkedHashMap<>();
    payload.put("isbn", request.isbn().replace("-", ""));
    payload.put("authors", request.authors());
    payload.put("publisher", blank(request.publisher()));
    payload.put("edition", blank(request.edition()));
    payload.put("publishedYear", request.publishedYear());
    payload.put("language", blank(request.language()));
    payload.put("category", request.category().trim());
    payload.put("tags", request.tags() == null ? List.of() : request.tags());
    payload.put("summary", blank(request.summary()));
    payload.put("coverImage", blank(request.coverImage()));
    return json(payload);
  }

  private String holdingPayload(LibraryBookUpsertRequest request) {
    return json(
        Map.of(
            "callNumber", request.callNumber().trim(),
            "location", request.location().trim(),
            "totalCount", request.totalCount(),
            "availableCount", request.availableCount(),
            "availabilityStatus", request.availableCount() > 0 ? "AVAILABLE" : "UNAVAILABLE"));
  }

  private BookResponse mapBook(ResultSet resultSet, int row) throws SQLException {
    Map<String, Object> book = json(resultSet, "book_payload");
    Map<String, Object> holding = json(resultSet, "holding_payload");
    int availableCount = integer(holding.get("availableCount"));
    return new BookResponse(
        resultSet.getObject("id", UUID.class),
        resultSet.getObject("holding_id", UUID.class),
        resultSet.getString("code"),
        resultSet.getString("name"),
        string(book.get("isbn")),
        list(book.get("authors")),
        string(book.get("publisher")),
        string(book.get("edition")),
        nullableInteger(book.get("publishedYear")),
        string(book.get("language")),
        string(book.get("category")),
        list(book.get("tags")),
        string(book.get("summary")),
        string(book.get("coverImage")),
        string(holding.get("callNumber")),
        string(holding.get("location")),
        integer(holding.get("totalCount")),
        availableCount,
        availableCount > 0);
  }

  private LoanResponse mapLoan(ResultSet resultSet, int row) throws SQLException {
    Map<String, Object> book = json(resultSet, "book_payload");
    Map<String, Object> holding = json(resultSet, "holding_payload");
    OffsetDateTime returned = resultSet.getObject("returned_at", OffsetDateTime.class);
    return new LoanResponse(
        resultSet.getObject("id", UUID.class),
        resultSet.getObject("book_id", UUID.class),
        resultSet.getString("name"),
        string(book.get("coverImage")),
        String.join("、", list(book.get("authors"))),
        string(holding.get("callNumber")),
        string(holding.get("location")),
        resultSet.getString("status"),
        resultSet.getObject("borrowed_at", OffsetDateTime.class).toInstant(),
        returned == null ? null : returned.toInstant());
  }

  private Map<String, Object> json(ResultSet resultSet, String column) throws SQLException {
    try {
      return objectMapper.readValue(resultSet.getString(column), MAP_TYPE);
    } catch (JsonProcessingException exception) {
      throw new SQLException("Invalid library payload", exception);
    }
  }

  private String json(Map<String, Object> value) {
    try {
      return objectMapper.writeValueAsString(value);
    } catch (JsonProcessingException exception) {
      throw new IllegalArgumentException("Invalid library payload", exception);
    }
  }

  private String blank(String value) {
    return value == null ? "" : value.trim();
  }

  private String string(Object value) {
    return value == null ? "" : String.valueOf(value);
  }

  private int integer(Object value) {
    return value == null ? 0 : Integer.parseInt(String.valueOf(value));
  }

  private Integer nullableInteger(Object value) {
    return value == null ? null : integer(value);
  }

  private List<String> list(Object value) {
    return value instanceof List<?> items
        ? items.stream().map(String::valueOf).toList()
        : List.of();
  }
}
