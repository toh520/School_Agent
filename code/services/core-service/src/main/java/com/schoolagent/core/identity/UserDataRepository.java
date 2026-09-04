package com.schoolagent.core.identity;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.schoolagent.core.identity.IdentityDtos.AuthorizationResponse;
import com.schoolagent.core.identity.IdentityDtos.CleanupResult;
import com.schoolagent.core.identity.IdentityDtos.PreferenceResponse;
import com.schoolagent.core.identity.IdentityDtos.PreferenceUpdateRequest;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** Persists user preferences, per-scope authorization and traceable memory cleanup. */
@Repository
public class UserDataRepository {

  private static final TypeReference<List<String>> STRING_LIST = new TypeReference<>() {};

  private final JdbcTemplate jdbcTemplate;
  private final ObjectMapper objectMapper;

  public UserDataRepository(JdbcTemplate jdbcTemplate, ObjectMapper objectMapper) {
    this.jdbcTemplate = jdbcTemplate;
    this.objectMapper = objectMapper;
  }

  public PreferenceResponse preference(UUID userId) {
    return jdbcTemplate.queryForObject(
        """
        SELECT tastes, budget, avoidances, allergens, dietary_goal, updated_at
        FROM user_preference WHERE user_id = ?
        """,
        this::mapPreference,
        userId);
  }

  public void initialize(UUID userId) {
    jdbcTemplate.update("INSERT INTO user_preference(user_id) VALUES (?)", userId);
    for (DataScope scope : DataScope.values()) {
      jdbcTemplate.update(
          "INSERT INTO data_authorization(user_id, data_scope, granted) VALUES (?, ?, FALSE)",
          userId,
          scope.name());
    }
  }

  public PreferenceResponse updatePreference(UUID userId, PreferenceUpdateRequest request) {
    jdbcTemplate.update(
        """
        UPDATE user_preference
        SET tastes = CAST(? AS jsonb), budget = ?, avoidances = CAST(? AS jsonb),
            allergens = CAST(? AS jsonb), dietary_goal = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        json(request.tastes()),
        request.budget(),
        json(request.avoidances()),
        json(request.allergens()),
        blankToNull(request.dietaryGoal()),
        userId);
    return preference(userId);
  }

  public Map<DataScope, AuthorizationResponse> authorizations(UUID userId) {
    Map<DataScope, AuthorizationResponse> result = new EnumMap<>(DataScope.class);
    jdbcTemplate.query(
        """
        SELECT data_scope, granted, changed_at
        FROM data_authorization WHERE user_id = ? ORDER BY data_scope
        """,
        resultSet -> {
          DataScope scope = DataScope.valueOf(resultSet.getString("data_scope"));
          result.put(
              scope,
              new AuthorizationResponse(
                  scope,
                  resultSet.getBoolean("granted"),
                  resultSet.getObject("changed_at", OffsetDateTime.class).toInstant()));
        },
        userId);
    return result;
  }

  public AuthorizationResponse updateAuthorization(UUID userId, DataScope scope, boolean granted) {
    jdbcTemplate.update(
        """
        UPDATE data_authorization
        SET granted = ?, changed_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND data_scope = ?
        """,
        granted,
        userId,
        scope.name());
    return authorizations(userId).get(scope);
  }

  public CleanupResult cleanup(UUID userId, DataScope scope, String triggerType) {
    int deleted =
        jdbcTemplate.update(
            "DELETE FROM user_long_term_memory WHERE user_id = ? AND data_scope = ?",
            userId,
            scope.name());
    // Basic exam records remain user-controlled after consent withdrawal. Only AI-derived
    // plans, practice evidence, and mastery summaries are removed for their matching scope.
    if (scope == DataScope.EXAMS) {
      deleted += jdbcTemplate.update("DELETE FROM review_plan WHERE user_id = ?", userId);
      deleted +=
          jdbcTemplate.update(
              "DELETE FROM learning_activity WHERE user_id = ? AND activity_type = 'PLAN'", userId);
    }
    if (scope == DataScope.MASTERY) {
      deleted += jdbcTemplate.update("DELETE FROM practice_item WHERE user_id = ?", userId);
      deleted += jdbcTemplate.update("DELETE FROM knowledge_mastery WHERE user_id = ?", userId);
      deleted +=
          jdbcTemplate.update(
              "DELETE FROM learning_activity WHERE user_id = ? AND activity_type <> 'PLAN'",
              userId);
    }
    UUID recordId = UUID.randomUUID();
    Instant completedAt = Instant.now();
    jdbcTemplate.update(
        """
        INSERT INTO data_cleanup_record(
            id, user_id, data_scope, trigger_type, status, deleted_records, completed_at)
        VALUES (?, ?, ?, ?, 'COMPLETED', ?, ?)
        """,
        recordId,
        userId,
        scope.name(),
        triggerType,
        deleted,
        OffsetDateTime.ofInstant(completedAt, ZoneOffset.UTC));
    return new CleanupResult(recordId, scope, deleted, completedAt);
  }

  private PreferenceResponse mapPreference(ResultSet resultSet, int rowNumber) throws SQLException {
    return new PreferenceResponse(
        stringList(resultSet.getString("tastes")),
        resultSet.getBigDecimal("budget"),
        stringList(resultSet.getString("avoidances")),
        stringList(resultSet.getString("allergens")),
        resultSet.getString("dietary_goal"),
        resultSet.getObject("updated_at", OffsetDateTime.class).toInstant());
  }

  private String json(List<String> values) {
    try {
      return objectMapper.writeValueAsString(values == null ? List.of() : values);
    } catch (JsonProcessingException exception) {
      throw new IllegalArgumentException("Invalid preference values", exception);
    }
  }

  private List<String> stringList(String value) throws SQLException {
    try {
      return objectMapper.readValue(value, STRING_LIST);
    } catch (JsonProcessingException exception) {
      throw new SQLException("Invalid preference JSON", exception);
    }
  }

  private String blankToNull(String value) {
    return value == null || value.isBlank() ? null : value.trim();
  }
}
