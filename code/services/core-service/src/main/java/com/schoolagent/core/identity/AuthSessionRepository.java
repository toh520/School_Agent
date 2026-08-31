package com.schoolagent.core.identity;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** Stores only refresh-token hashes and provides immediate access-token revocation checks. */
@Repository
public class AuthSessionRepository {

  private final JdbcTemplate jdbcTemplate;

  public AuthSessionRepository(JdbcTemplate jdbcTemplate) {
    this.jdbcTemplate = jdbcTemplate;
  }

  public UUID create(UUID userId, String refreshTokenHash, Instant expiresAt) {
    UUID id = UUID.randomUUID();
    jdbcTemplate.update(
        """
        INSERT INTO auth_session(id, user_id, refresh_token_hash, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        id,
        userId,
        refreshTokenHash,
        OffsetDateTime.ofInstant(expiresAt, ZoneOffset.UTC));
    return id;
  }

  public Optional<SessionRecord> findActiveByRefreshHash(String hash) {
    return jdbcTemplate
        .query(
            """
            SELECT s.id, s.user_id, s.expires_at
            FROM auth_session s
            JOIN app_user u ON u.id = s.user_id
            WHERE s.refresh_token_hash = ? AND s.revoked_at IS NULL
              AND s.expires_at > CURRENT_TIMESTAMP AND u.status = 'ACTIVE'
            """,
            this::mapSession,
            hash)
        .stream()
        .findFirst();
  }

  public boolean isActive(UUID sessionId, UUID userId) {
    Integer count =
        jdbcTemplate.queryForObject(
            """
            SELECT COUNT(*) FROM auth_session s
            JOIN app_user u ON u.id = s.user_id
            WHERE s.id = ? AND s.user_id = ? AND s.revoked_at IS NULL
              AND s.expires_at > CURRENT_TIMESTAMP AND u.status = 'ACTIVE'
            """,
            Integer.class,
            sessionId,
            userId);
    return count != null && count == 1;
  }

  public void rotate(UUID sessionId, String newHash, Instant newExpiry) {
    jdbcTemplate.update(
        """
        UPDATE auth_session
        SET refresh_token_hash = ?, expires_at = ?, last_used_at = CURRENT_TIMESTAMP
        WHERE id = ? AND revoked_at IS NULL
        """,
        newHash,
        OffsetDateTime.ofInstant(newExpiry, ZoneOffset.UTC),
        sessionId);
  }

  public void revoke(UUID sessionId, UUID userId) {
    jdbcTemplate.update(
        """
        UPDATE auth_session SET revoked_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ? AND revoked_at IS NULL
        """,
        sessionId,
        userId);
  }

  private SessionRecord mapSession(ResultSet resultSet, int rowNumber) throws SQLException {
    return new SessionRecord(
        resultSet.getObject("id", UUID.class),
        resultSet.getObject("user_id", UUID.class),
        resultSet.getObject("expires_at", OffsetDateTime.class).toInstant());
  }

  public record SessionRecord(UUID id, UUID userId, Instant expiresAt) {}
}
