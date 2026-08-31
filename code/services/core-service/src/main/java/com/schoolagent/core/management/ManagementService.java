package com.schoolagent.core.management;

import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.management.ManagementDtos.AccountSummary;
import com.schoolagent.core.management.ManagementDtos.FieldError;
import com.schoolagent.core.management.ManagementDtos.ImportPreview;
import com.schoolagent.core.management.ManagementDtos.ManagedResourceResponse;
import com.schoolagent.core.management.ManagementDtos.OperationLogResponse;
import com.schoolagent.core.management.ManagementDtos.ResourceSchemaResponse;
import com.schoolagent.core.web.BusinessException;
import com.schoolagent.core.web.ErrorCode;
import com.schoolagent.core.web.PageResponse;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** M03 application service for validated administration and traceable writes. */
@Service
public class ManagementService {

  private final ManagementRepository repository;
  private final ResourceValidator validator;
  private final CsvTableParser csvParser;

  public ManagementService(
      ManagementRepository repository, ResourceValidator validator, CsvTableParser csvParser) {
    this.repository = repository;
    this.validator = validator;
    this.csvParser = csvParser;
  }

  public List<ResourceSchemaResponse> schemas() {
    return List.of(ResourceType.values()).stream().map(this::schema).toList();
  }

  public ResourceSchemaResponse schema(ResourceType type) {
    String header =
        String.join(",", ResourceSchema.fields(type).stream().map(FieldDefinition::key).toList());
    return new ResourceSchemaResponse(
        type, type.displayName(), ResourceSchema.fields(type), header);
  }

  public PageResponse<ManagedResourceResponse> search(
      ResourceType type, String query, String status, int page, int size) {
    PageResponse<ManagedResource> result = repository.search(type, query, status, page, size);
    return new PageResponse<>(
        result.items().stream().map(this::response).toList(),
        result.page(),
        result.size(),
        result.total(),
        result.totalPages());
  }

  @Transactional
  public ManagedResourceResponse create(
      CurrentIdentity actor, ResourceType type, Map<String, Object> rawValues, String requestId) {
    ValidationResult validation = validator.validate(type, rawValues, null, 0);
    requireValid(validation);
    try {
      ManagedResource resource = repository.create(type, validation.values(), actor.userId());
      log(actor, "CREATE", resource, type.displayName() + "已新增", requestId);
      return response(resource);
    } catch (DuplicateKeyException exception) {
      throw new BusinessException(ErrorCode.CONFLICT, HttpStatus.CONFLICT);
    }
  }

  @Transactional
  public ManagedResourceResponse update(
      CurrentIdentity actor,
      ResourceType type,
      UUID id,
      Map<String, Object> rawValues,
      String requestId) {
    requireResource(type, id);
    ValidationResult validation = validator.validate(type, rawValues, id, 0);
    requireValid(validation);
    try {
      ManagedResource resource = repository.update(type, id, validation.values(), actor.userId());
      log(actor, "UPDATE", resource, type.displayName() + "已更新", requestId);
      return response(resource);
    } catch (DuplicateKeyException exception) {
      throw new BusinessException(ErrorCode.CONFLICT, HttpStatus.CONFLICT);
    }
  }

  @Transactional
  public void deactivate(CurrentIdentity actor, ResourceType type, UUID id, String requestId) {
    ManagedResource resource = requireResource(type, id);
    if (repository.hasActiveChildren(type, resource.code())) {
      throw new BusinessException(ErrorCode.RESOURCE_IN_USE, HttpStatus.CONFLICT);
    }
    if (!repository.deactivate(type, id, actor.userId())) {
      throw new BusinessException(ErrorCode.RESOURCE_NOT_FOUND, HttpStatus.NOT_FOUND);
    }
    log(actor, "DEACTIVATE", resource, type.displayName() + "已停用", requestId);
  }

  public ImportPreview validateImport(ResourceType type, String csvContent) {
    return importRows(type, csvContent, false, null, null);
  }

  @Transactional
  public ImportPreview commitImport(
      CurrentIdentity actor, ResourceType type, String csvContent, String requestId) {
    return importRows(type, csvContent, true, actor, requestId);
  }

  public PageResponse<AccountSummary> accounts(String query, String status, int page, int size) {
    return repository.searchAccounts(query, status, page, size);
  }

  @Transactional
  public void updateAccountStatus(
      CurrentIdentity actor, UUID userId, String status, String requestId) {
    if (actor.userId().equals(userId)) {
      throw new BusinessException(ErrorCode.SELF_STATUS_CHANGE_FORBIDDEN, HttpStatus.CONFLICT);
    }
    if (!repository.updateAccountStatus(userId, status)) {
      throw new BusinessException(ErrorCode.RESOURCE_NOT_FOUND, HttpStatus.NOT_FOUND);
    }
    repository.logOperation(
        actor.userId(),
        "ACCOUNT_STATUS",
        "ACCOUNT",
        userId.toString(),
        null,
        "账号状态更新为 " + status,
        requestId);
  }

  public PageResponse<OperationLogResponse> operationLogs(int page, int size) {
    return repository.operationLogs(page, size);
  }

  private ImportPreview importRows(
      ResourceType type,
      String csvContent,
      boolean commit,
      CurrentIdentity actor,
      String requestId) {
    List<Map<String, String>> rows;
    try {
      rows = csvParser.parse(csvContent);
    } catch (IllegalArgumentException exception) {
      return new ImportPreview(
          type, 0, 0, List.of(new FieldError(1, "csv", exception.getMessage())), List.of(), false);
    }
    if (rows.isEmpty()) {
      return new ImportPreview(
          type, 0, 0, List.of(new FieldError(1, "csv", "CSV 没有数据行")), List.of(), false);
    }

    List<FieldError> errors = new ArrayList<>();
    List<ValidationResult> validRows = new ArrayList<>();
    Set<String> codes = new HashSet<>();
    for (int index = 0; index < rows.size(); index++) {
      int csvRow = index + 2;
      ValidationResult result = validator.validate(type, rows.get(index), null, csvRow);
      errors.addAll(result.errors());
      String code =
          String.valueOf(result.values().getOrDefault("code", "")).toUpperCase(Locale.ROOT);
      if (!code.isBlank() && !codes.add(code)) {
        errors.add(new FieldError(csvRow, "code", "CSV 内编码重复"));
      }
      if (result.valid()) {
        validRows.add(result);
      }
    }
    List<ManagedResourceResponse> preview =
        validRows.stream().limit(20).map(row -> previewResponse(type, row)).toList();
    if (!errors.isEmpty() || !commit) {
      return new ImportPreview(
          type, rows.size(), rows.size() - errorRows(errors), errors, preview, false);
    }

    List<ManagedResourceResponse> committedResources = new ArrayList<>();
    try {
      for (ValidationResult row : validRows) {
        ManagedResource resource = repository.create(type, row.values(), actor.userId());
        log(actor, "IMPORT", resource, type.displayName() + "由 CSV 导入", requestId);
        committedResources.add(response(resource));
      }
    } catch (DuplicateKeyException exception) {
      throw new BusinessException(ErrorCode.CONFLICT, HttpStatus.CONFLICT);
    }
    return new ImportPreview(type, rows.size(), rows.size(), List.of(), committedResources, true);
  }

  private ManagedResource requireResource(ResourceType type, UUID id) {
    return repository
        .findById(type, id)
        .orElseThrow(
            () -> new BusinessException(ErrorCode.RESOURCE_NOT_FOUND, HttpStatus.NOT_FOUND));
  }

  private void requireValid(ValidationResult validation) {
    if (!validation.valid()) {
      boolean duplicateCode =
          validation.errors().stream()
              .anyMatch(error -> "code".equals(error.field()) && "编码已存在".equals(error.message()));
      if (duplicateCode) {
        throw new BusinessException(ErrorCode.CONFLICT, HttpStatus.CONFLICT);
      }
      throw new BusinessException(ErrorCode.INVALID_REQUEST, HttpStatus.BAD_REQUEST);
    }
  }

  private void log(
      CurrentIdentity actor,
      String action,
      ManagedResource resource,
      String summary,
      String requestId) {
    repository.logOperation(
        actor.userId(),
        action,
        resource.type().name(),
        resource.id().toString(),
        resource.code(),
        summary,
        requestId);
  }

  private ManagedResourceResponse response(ManagedResource resource) {
    Map<String, Object> values = new LinkedHashMap<>();
    values.put("code", resource.code());
    values.put("name", resource.name());
    if (resource.type().parentField() != null) {
      values.put(resource.type().parentField(), resource.parentCode());
    }
    values.putAll(resource.payload());
    values.put("source", resource.source());
    int completeness = validator.validate(resource.type(), values, resource.id(), 0).completeness();
    return new ManagedResourceResponse(
        resource.id(),
        resource.type(),
        Map.copyOf(values),
        resource.status(),
        completeness,
        resource.createdBy(),
        resource.updatedBy(),
        resource.createdAt(),
        resource.updatedAt());
  }

  private ManagedResourceResponse previewResponse(ResourceType type, ValidationResult result) {
    return new ManagedResourceResponse(
        null,
        type,
        result.values(),
        "ACTIVE",
        result.completeness(),
        null,
        null,
        Instant.EPOCH,
        Instant.EPOCH);
  }

  private int errorRows(List<FieldError> errors) {
    return (int) errors.stream().map(FieldError::row).filter(row -> row > 1).distinct().count();
  }
}
