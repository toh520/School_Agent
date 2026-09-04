package com.schoolagent.core.exam;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.UUID;

/** Public contracts for AI-independent exam schedule management. */
public final class ExamDtos {
  private ExamDtos() {}

  public record ExamUpsertRequest(
      @NotBlank @Size(max = 120) String subject,
      @NotNull LocalDate examDate,
      @NotNull LocalTime startTime,
      @NotNull LocalTime endTime,
      @NotBlank @Size(max = 200) String location) {}

  public record ExamResponse(
      UUID id,
      String subject,
      LocalDate examDate,
      LocalTime startTime,
      LocalTime endTime,
      String location,
      Instant createdAt,
      Instant updatedAt) {}
}
