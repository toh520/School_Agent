package com.schoolagent.core.identity;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** Database access for account state and non-core profile fields. */
@Repository
public class UserRepository {

  private final JdbcTemplate jdbcTemplate;

  public UserRepository(JdbcTemplate jdbcTemplate) {
    this.jdbcTemplate = jdbcTemplate;
  }

  public Optional<UserAccount> findByUsername(String username) {
    return jdbcTemplate
        .query(
            """
            SELECT id, username, password_hash, student_number, real_name, phone, role, status,
                   nickname, avatar_url, contact, created_at, updated_at
            FROM app_user
            WHERE lower(username) = lower(?)
            """,
            this::mapUser,
            username.trim())
        .stream()
        .findFirst();
  }

  public Optional<UserAccount> findById(UUID id) {
    return jdbcTemplate
        .query(
            """
            SELECT id, username, password_hash, student_number, real_name, phone, role, status,
                   nickname, avatar_url, contact, created_at, updated_at
            FROM app_user WHERE id = ?
            """,
            this::mapUser,
            id)
        .stream()
        .findFirst();
  }

  public UserAccount updateProfile(UUID id, String nickname, String avatarUrl, String contact) {
    jdbcTemplate.update(
        """
        UPDATE app_user
        SET nickname = ?, avatar_url = ?, contact = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        nickname.trim(),
        blankToNull(avatarUrl),
        blankToNull(contact),
        id);
    return findById(id).orElseThrow();
  }

  public boolean existsByUsername(String username) {
    return exists("SELECT COUNT(*) FROM app_user WHERE lower(username) = lower(?)", username);
  }

  public boolean existsByStudentNumber(String studentNumber) {
    return exists("SELECT COUNT(*) FROM app_user WHERE student_number = ?", studentNumber);
  }

  public boolean existsByPhone(String phone) {
    return exists("SELECT COUNT(*) FROM app_user WHERE phone = ?", phone);
  }

  public UserAccount createStudent(
      String username, String passwordHash, String studentNumber, String realName, String phone) {
    UUID id = UUID.randomUUID();
    jdbcTemplate.update(
        """
        INSERT INTO app_user(
            id, username, password_hash, student_number, real_name, phone, role, nickname)
        VALUES (?, ?, ?, ?, ?, ?, 'STUDENT', ?)
        """,
        id,
        username.trim(),
        passwordHash,
        studentNumber.trim(),
        realName.trim(),
        phone.trim(),
        realName.trim());
    return findById(id).orElseThrow();
  }

  private UserAccount mapUser(ResultSet resultSet, int rowNumber) throws SQLException {
    return new UserAccount(
        resultSet.getObject("id", UUID.class),
        resultSet.getString("username"),
        resultSet.getString("password_hash"),
        resultSet.getString("student_number"),
        resultSet.getString("real_name"),
        resultSet.getString("phone"),
        UserRole.valueOf(resultSet.getString("role")),
        resultSet.getString("status"),
        resultSet.getString("nickname"),
        resultSet.getString("avatar_url"),
        resultSet.getString("contact"),
        instant(resultSet, "created_at"),
        instant(resultSet, "updated_at"));
  }

  private boolean exists(String sql, String value) {
    Integer count = jdbcTemplate.queryForObject(sql, Integer.class, value.trim());
    return count != null && count > 0;
  }

  private Instant instant(ResultSet resultSet, String column) throws SQLException {
    return resultSet.getObject(column, OffsetDateTime.class).toInstant();
  }

  private String blankToNull(String value) {
    return value == null || value.isBlank() ? null : value.trim();
  }
}
