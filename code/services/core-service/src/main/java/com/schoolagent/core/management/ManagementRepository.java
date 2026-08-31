package com.schoolagent.core.management;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.schoolagent.core.management.ManagementDtos.AccountSummary;
import com.schoolagent.core.management.ManagementDtos.OperationLogResponse;
import com.schoolagent.core.web.PageResponse;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** JDBC access for M03 tables; all dynamic identifiers originate from ResourceType. */
@Repository
class ManagementRepository {

  private static final TypeReference<LinkedHashMap<String, Object>> MAP_TYPE =
      new TypeReference<>() {};

  private final JdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;

  ManagementRepository(JdbcTemplate jdbcTemplate, ObjectMapper objectMapper) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
  }

  PageResponse<ManagedResource> search(
      ResourceType type, String query, String status, int page, int size) {
    boolean inactive = "INACTIVE".equalsIgnoreCase(status);
    StringBuilder where =
        new StringBuilder(inactive ? " WHERE deleted_at IS NOT NULL" : " WHERE deleted_at IS NULL");
    List<Object> parameters = new ArrayList<>();
    if (query != null && !query.isBlank()) {
      where.append(" AND (code ILIKE ? OR name ILIKE ? OR payload::text ILIKE ?)");
      String pattern = "%" + query.trim() + "%";
      parameters.add(pattern);
      parameters.add(pattern);
      parameters.add(pattern);
    }
    if (status != null && !status.isBlank()) {
      where.append(" AND status = ?");
      parameters.add(status.trim().toUpperCase());
    }
    String table = type.tableName();
    Long total =
        jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM " + table + where, Long.class, parameters.toArray());
    List<Object> pageParameters = new ArrayList<>(parameters);
    pageParameters.add(size);
    pageParameters.add((long) page * size);
    List<ManagedResource> items =
        jdbcTemplate.query(
            "SELECT * FROM " + table + where + " ORDER BY updated_at DESC, name LIMIT ? OFFSET ?",
            (resultSet, rowNumber) -> mapResource(resultSet, type),
            pageParameters.toArray());
    return page(items, page, size, total);
  }

  Optional<ManagedResource> findById(ResourceType type, UUID id) {
    return jdbcTemplate
        .query(
            "SELECT * FROM " + type.tableName() + " WHERE id = ? AND deleted_at IS NULL",
            (resultSet, rowNumber) -> mapResource(resultSet, type),
            id)
        .stream()
        .findFirst();
  }

  ManagedResource create(ResourceType type, Map<String, Object> values, UUID actorUserId) {
    UUID id = UUID.randomUUID();
    jdbcTemplate.update(
        "INSERT INTO "
            + type.tableName()
            + "(id, code, name, parent_code, payload, source, status, created_by, updated_by) "
            + "VALUES (?, ?, ?, ?, ?::jsonb, ?, 'ACTIVE', ?, ?)",
        id,
        values.get("code"),
        values.get("name"),
        parentCode(type, values),
        payload(type, values),
        values.get("source"),
        actorUserId,
        actorUserId);
    return findById(type, id).orElseThrow();
  }

  ManagedResource update(ResourceType type, UUID id, Map<String, Object> values, UUID actorUserId) {
    jdbcTemplate.update(
        "UPDATE "
            + type.tableName()
            + " SET code = ?, name = ?, parent_code = ?, payload = ?::jsonb, source = ?, "
            + "updated_by = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        values.get("code"),
        values.get("name"),
        parentCode(type, values),
        payload(type, values),
        values.get("source"),
        actorUserId,
        id);
    return findById(type, id).orElseThrow();
  }

  boolean deactivate(ResourceType type, UUID id, UUID actorUserId) {
    return jdbcTemplate.update(
            "UPDATE "
                + type.tableName()
                + " SET status = 'INACTIVE', deleted_at = CURRENT_TIMESTAMP, "
                + "updated_by = ?, updated_at = CURRENT_TIMESTAMP "
                + "WHERE id = ? AND deleted_at IS NULL",
            actorUserId,
            id)
        > 0;
  }

  boolean existsCode(ResourceType type, String code, UUID excludedId) {
    String sql =
        "SELECT COUNT(*) FROM "
            + type.tableName()
            + " WHERE lower(code) = lower(?) AND deleted_at IS NULL";
    List<Object> parameters = new ArrayList<>(List.of(code));
    if (excludedId != null) {
      sql += " AND id <> ?";
      parameters.add(excludedId);
    }
    Long count = jdbcTemplate.queryForObject(sql, Long.class, parameters.toArray());
    return count != null && count > 0;
  }

  boolean hasActiveChildren(ResourceType type, String code) {
    ResourceType child =
        switch (type) {
          case CANTEEN -> ResourceType.STALL;
          case STALL -> ResourceType.DISH;
          case BOOK -> ResourceType.HOLDING;
          default -> null;
        };
    if (child == null) {
      return false;
    }
    Long count =
        jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM "
                + child.tableName()
                + " WHERE parent_code = ? AND deleted_at IS NULL",
            Long.class,
            code);
    return count != null && count > 0;
  }

  PageResponse<AccountSummary> searchAccounts(String query, String status, int page, int size) {
    StringBuilder where = new StringBuilder(" WHERE 1 = 1");
    List<Object> parameters = new ArrayList<>();
    if (query != null && !query.isBlank()) {
      where.append(" AND (username ILIKE ? OR nickname ILIKE ?)");
      String pattern = "%" + query.trim() + "%";
      parameters.add(pattern);
      parameters.add(pattern);
    }
    if (status != null && !status.isBlank()) {
      where.append(" AND status = ?");
      parameters.add(status.trim());
    }
    Long total =
        jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM app_user" + where, Long.class, parameters.toArray());
    List<Object> pageParameters = new ArrayList<>(parameters);
    pageParameters.add(size);
    pageParameters.add((long) page * size);
    List<AccountSummary> items =
        jdbcTemplate.query(
            "SELECT id, username, role, status, nickname, created_at, updated_at FROM app_user"
                + where
                + " ORDER BY created_at DESC LIMIT ? OFFSET ?",
            this::mapAccount,
            pageParameters.toArray());
    return page(items, page, size, total);
  }

  boolean updateAccountStatus(UUID userId, String status) {
    return jdbcTemplate.update(
            "UPDATE app_user SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            status,
            userId)
        > 0;
  }

  void logOperation(
      UUID actorUserId,
      String action,
      String resourceType,
      String resourceId,
      String resourceCode,
      String summary,
      String requestId) {
    jdbcTemplate.update(
        """
        INSERT INTO admin_operation_log(
            actor_user_id, action, resource_type, resource_id, resource_code, summary, request_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        actorUserId,
        action,
        resourceType,
        resourceId,
        resourceCode,
        summary,
        requestId);
  }

  PageResponse<OperationLogResponse> operationLogs(int page, int size) {
    Long total =
        jdbcTemplate.queryForObject("SELECT COUNT(*) FROM admin_operation_log", Long.class);
    List<OperationLogResponse> items =
        jdbcTemplate.query(
            """
            SELECT log.id, log.actor_user_id, actor.username AS actor_username, log.action,
                   log.resource_type, log.resource_id, log.resource_code, log.summary,
                   log.request_id, log.occurred_at
            FROM admin_operation_log log
            LEFT JOIN app_user actor ON actor.id = log.actor_user_id
            ORDER BY log.occurred_at DESC, log.id DESC LIMIT ? OFFSET ?
            """,
            this::mapOperation,
            size,
            (long) page * size);
    return page(items, page, size, total);
  }

  private ManagedResource mapResource(ResultSet resultSet, ResourceType type) throws SQLException {
    try {
      return new ManagedResource(
          resultSet.getObject("id", UUID.class),
          type,
          resultSet.getString("code"),
          resultSet.getString("name"),
          resultSet.getString("parent_code"),
          objectMapper.readValue(resultSet.getString("payload"), MAP_TYPE),
          resultSet.getString("source"),
          resultSet.getString("status"),
          resultSet.getObject("created_by", UUID.class),
          resultSet.getObject("updated_by", UUID.class),
          instant(resultSet, "created_at"),
          instant(resultSet, "updated_at"));
    } catch (JsonProcessingException exception) {
      throw new SQLException("Invalid managed payload", exception);
    }
  }

  private AccountSummary mapAccount(ResultSet resultSet, int rowNumber) throws SQLException {
    return new AccountSummary(
        resultSet.getObject("id", UUID.class),
        resultSet.getString("username"),
        resultSet.getString("role"),
        resultSet.getString("status"),
        resultSet.getString("nickname"),
        instant(resultSet, "created_at"),
        instant(resultSet, "updated_at"));
  }

  private OperationLogResponse mapOperation(ResultSet resultSet, int rowNumber)
      throws SQLException {
    return new OperationLogResponse(
        resultSet.getLong("id"),
        resultSet.getObject("actor_user_id", UUID.class),
        resultSet.getString("actor_username"),
        resultSet.getString("action"),
        resultSet.getString("resource_type"),
        resultSet.getString("resource_id"),
        resultSet.getString("resource_code"),
        resultSet.getString("summary"),
        resultSet.getString("request_id"),
        instant(resultSet, "occurred_at"));
  }

  private String payload(ResourceType type, Map<String, Object> values) {
    Map<String, Object> payload = new LinkedHashMap<>(values);
    payload.remove("code");
    payload.remove("name");
    payload.remove("source");
    if (type.parentField() != null) {
      payload.remove(type.parentField());
    }
    try {
      return objectMapper.writeValueAsString(payload);
    } catch (JsonProcessingException exception) {
      throw new IllegalArgumentException("Managed values cannot be serialized", exception);
    }
  }

  private String parentCode(ResourceType type, Map<String, Object> values) {
    return type.parentField() == null ? null : String.valueOf(values.get(type.parentField()));
  }

  private Instant instant(ResultSet resultSet, String column) throws SQLException {
    return resultSet.getObject(column, OffsetDateTime.class).toInstant();
  }

  private <T> PageResponse<T> page(List<T> items, int page, int size, Long total) {
    long count = total == null ? 0 : total;
    int totalPages = count == 0 ? 0 : (int) ((count + size - 1) / size);
    return new PageResponse<>(items, page, size, count, totalPages);
  }
}
