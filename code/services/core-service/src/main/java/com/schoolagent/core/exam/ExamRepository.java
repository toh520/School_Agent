package com.schoolagent.core.exam;

import com.schoolagent.core.exam.ExamDtos.ExamResponse;
import com.schoolagent.core.exam.ExamDtos.ExamUpsertRequest;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

/** JDBC access for exam records; every personal query requires the authenticated user id. */
@Repository
class ExamRepository {
  private final JdbcTemplate jdbc;

  ExamRepository(JdbcTemplate jdbc) {
    this.jdbc = jdbc;
  }

  List<ExamResponse> list(UUID userId) {
    return jdbc.query(
        """
        SELECT id, subject, exam_date, start_time, end_time, location, created_at, updated_at
        FROM exam_record
        WHERE user_id = ?
        ORDER BY exam_date, start_time, id
        """,
        this::map,
        userId);
  }

  Optional<ExamResponse> find(UUID userId, UUID examId) {
    return jdbc
        .query(
            """
            SELECT id, subject, exam_date, start_time, end_time, location, created_at, updated_at
            FROM exam_record WHERE user_id = ? AND id = ?
            """,
            this::map,
            userId,
            examId)
        .stream()
        .findFirst();
  }

  Optional<ExamResponse> next(UUID userId) {
    return jdbc
        .query(
            """
            SELECT id, subject, exam_date, start_time, end_time, location, created_at, updated_at
            FROM exam_record
            WHERE user_id = ?
              AND (exam_date + end_time) >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Shanghai')
            ORDER BY exam_date, start_time, id
            LIMIT 1
            """,
            this::map,
            userId)
        .stream()
        .findFirst();
  }

  ExamResponse create(UUID userId, ExamUpsertRequest request) {
    UUID id = UUID.randomUUID();
    jdbc.update(
        """
        INSERT INTO exam_record(id, user_id, subject, exam_date, start_time, end_time, location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        id,
        userId,
        request.subject().trim(),
        request.examDate(),
        request.startTime(),
        request.endTime(),
        request.location().trim());
    return find(userId, id).orElseThrow();
  }

  Optional<ExamResponse> update(UUID userId, UUID examId, ExamUpsertRequest request) {
    int changed =
        jdbc.update(
            """
            UPDATE exam_record
            SET subject = ?, exam_date = ?, start_time = ?, end_time = ?, location = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND id = ?
            """,
            request.subject().trim(),
            request.examDate(),
            request.startTime(),
            request.endTime(),
            request.location().trim(),
            userId,
            examId);
    return changed == 0 ? Optional.empty() : find(userId, examId);
  }

  boolean delete(UUID userId, UUID examId) {
    return jdbc.update("DELETE FROM exam_record WHERE user_id = ? AND id = ?", userId, examId) > 0;
  }

  private ExamResponse map(ResultSet resultSet, int row) throws SQLException {
    return new ExamResponse(
        resultSet.getObject("id", UUID.class),
        resultSet.getString("subject"),
        resultSet.getObject("exam_date", java.time.LocalDate.class),
        resultSet.getObject("start_time", java.time.LocalTime.class),
        resultSet.getObject("end_time", java.time.LocalTime.class),
        resultSet.getString("location"),
        resultSet.getObject("created_at", OffsetDateTime.class).toInstant(),
        resultSet.getObject("updated_at", OffsetDateTime.class).toInstant());
  }
}
