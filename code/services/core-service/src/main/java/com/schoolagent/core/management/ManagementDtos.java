package com.schoolagent.core.management;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** API records for the M03 unified information administration boundary. */
public final class ManagementDtos {

  private ManagementDtos() {}

  public record ResourceSchemaResponse(
      ResourceType type, String label, List<FieldDefinition> fields, String csvHeader) {}

  public record ResourceMutationRequest(@NotNull Map<String, Object> values) {}

  public record ManagedResourceResponse(
      UUID id,
      ResourceType type,
      Map<String, Object> values,
      String status,
      int completeness,
      UUID createdBy,
      UUID updatedBy,
      Instant createdAt,
      Instant updatedAt) {}

  public record FieldError(int row, String field, String message) {}

  public record ImportRequest(
      @NotNull ResourceType type, @NotBlank @Size(max = 524288) String csvContent) {}

  public record ImportPreview(
      ResourceType type,
      int totalRows,
      int validRows,
      List<FieldError> errors,
      List<ManagedResourceResponse> preview,
      boolean committed) {}

  public record AccountSummary(
      UUID id,
      String username,
      String role,
      String status,
      String nickname,
      Instant createdAt,
      Instant updatedAt) {}

  public record AccountStatusRequest(
      @NotBlank @Pattern(regexp = "ACTIVE|DISABLED") String status) {}

  public record OperationLogResponse(
      long id,
      UUID actorUserId,
      String actorUsername,
      String action,
      String resourceType,
      String resourceId,
      String resourceCode,
      String summary,
      String requestId,
      Instant occurredAt) {}
}
