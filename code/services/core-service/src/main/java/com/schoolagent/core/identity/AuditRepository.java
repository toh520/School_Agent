package com.schoolagent.core.identity;

import com.schoolagent.core.identity.IdentityDtos.AuditEventResponse;
import com.schoolagent.core.web.PageResponse;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** Append-only minimum audit store; it intentionally contains no request bodies or secrets. */
@Repository
public class AuditRepository {

  private final JdbcTemplate jdbcTemplate;

  public AuditRepository(JdbcTemplate jdbcTemplate) {
    this.jdbcTemplate = jdbcTemplate;
  }

  public void record(
      UUID userId,
      UUID actorUserId,
      String eventType,
      String module,
      String targetType,
      String targetId,
      String outcome,
      String requestId) {
    jdbcTemplate.update(
        """
        INSERT INTO audit_event(
            user_id, actor_user_id, event_type, module, target_type, target_id, outcome, request_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        userId,
        actorUserId,
        eventType,
        module,
        targetType,
        targetId,
        outcome,
        requestId);
  }

  public PageResponse<AuditEventResponse> search(
      UUID userId, String eventType, String module, Instant from, Instant to, int page, int size) {
    StringBuilder where = new StringBuilder(" WHERE 1 = 1");
    List<Object> parameters = new ArrayList<>();
    addFilter(where, parameters, "user_id = ?", userId);
    addFilter(where, parameters, "event_type = ?", blankToNull(eventType));
    addFilter(where, parameters, "module = ?", blankToNull(module));
    addFilter(where, parameters, "occurred_at >= ?", offset(from));
    addFilter(where, parameters, "occurred_at <= ?", offset(to));

    Long total =
        jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM audit_event" + where, Long.class, parameters.toArray());
    List<Object> pageParameters = new ArrayList<>(parameters);
    pageParameters.add(size);
    pageParameters.add((long) page * size);
    List<AuditEventResponse> items =
        jdbcTemplate.query(
            """
            SELECT id, user_id, actor_user_id, event_type, module, target_type, target_id,
                   outcome, request_id, occurred_at
            FROM audit_event
            """
                + where
                + " ORDER BY occurred_at DESC, id DESC LIMIT ? OFFSET ?",
            this::mapAudit,
            pageParameters.toArray());
    long count = total == null ? 0 : total;
    int totalPages = count == 0 ? 0 : (int) ((count + size - 1) / size);
    return new PageResponse<>(items, page, size, count, totalPages);
  }

  private void addFilter(
      StringBuilder where, List<Object> parameters, String expression, Object value) {
    if (value != null) {
      where.append(" AND ").append(expression);
      parameters.add(value);
    }
  }

  private AuditEventResponse mapAudit(ResultSet resultSet, int rowNumber) throws SQLException {
    return new AuditEventResponse(
        resultSet.getLong("id"),
        resultSet.getObject("user_id", UUID.class),
        resultSet.getObject("actor_user_id", UUID.class),
        resultSet.getString("event_type"),
        resultSet.getString("module"),
        resultSet.getString("target_type"),
        resultSet.getString("target_id"),
        resultSet.getString("outcome"),
        resultSet.getString("request_id"),
        resultSet.getObject("occurred_at", OffsetDateTime.class).toInstant());
  }

  private OffsetDateTime offset(Instant value) {
    return value == null ? null : OffsetDateTime.ofInstant(value, ZoneOffset.UTC);
  }

  private String blankToNull(String value) {
    return value == null || value.isBlank() ? null : value.trim();
  }
}
