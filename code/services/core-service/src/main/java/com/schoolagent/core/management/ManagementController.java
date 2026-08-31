package com.schoolagent.core.management;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.management.ManagementDtos.AccountStatusRequest;
import com.schoolagent.core.management.ManagementDtos.AccountSummary;
import com.schoolagent.core.management.ManagementDtos.ImportPreview;
import com.schoolagent.core.management.ManagementDtos.ImportRequest;
import com.schoolagent.core.management.ManagementDtos.ManagedResourceResponse;
import com.schoolagent.core.management.ManagementDtos.OperationLogResponse;
import com.schoolagent.core.management.ManagementDtos.ResourceMutationRequest;
import com.schoolagent.core.management.ManagementDtos.ResourceSchemaResponse;
import com.schoolagent.core.web.ApiResponse;
import com.schoolagent.core.web.PageResponse;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Single INFO_ADMIN boundary for all M03 data and account administration. */
@Validated
@RestController
@RequestMapping("/api/v1/admin/management")
@PreAuthorize("hasRole('INFO_ADMIN')")
public class ManagementController {

  private final ManagementService service;

  public ManagementController(ManagementService service) {
    this.service = service;
  }

  @GetMapping("/schemas")
  public ApiResponse<List<ResourceSchemaResponse>> schemas() {
    return ApiResponse.success(service.schemas(), requestId());
  }

  @GetMapping("/resources/{type}")
  public ApiResponse<PageResponse<ManagedResourceResponse>> resources(
      @PathVariable ResourceType type,
      @RequestParam(defaultValue = "") String query,
      @RequestParam(defaultValue = "") String status,
      @RequestParam(defaultValue = "0") @Min(0) int page,
      @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
    return ApiResponse.success(service.search(type, query, status, page, size), requestId());
  }

  @PostMapping("/resources/{type}")
  public ApiResponse<ManagedResourceResponse> create(
      Authentication authentication,
      @PathVariable ResourceType type,
      @Valid @RequestBody ResourceMutationRequest request) {
    return ApiResponse.success(
        service.create(CurrentIdentity.from(authentication), type, request.values(), requestId()),
        requestId());
  }

  @PutMapping("/resources/{type}/{id}")
  public ApiResponse<ManagedResourceResponse> update(
      Authentication authentication,
      @PathVariable ResourceType type,
      @PathVariable UUID id,
      @Valid @RequestBody ResourceMutationRequest request) {
    return ApiResponse.success(
        service.update(
            CurrentIdentity.from(authentication), type, id, request.values(), requestId()),
        requestId());
  }

  @DeleteMapping("/resources/{type}/{id}")
  public ApiResponse<Void> deactivate(
      Authentication authentication, @PathVariable ResourceType type, @PathVariable UUID id) {
    service.deactivate(CurrentIdentity.from(authentication), type, id, requestId());
    return ApiResponse.success(null, requestId());
  }

  @PostMapping("/imports/validate")
  public ApiResponse<ImportPreview> validateImport(@Valid @RequestBody ImportRequest request) {
    return ApiResponse.success(
        service.validateImport(request.type(), request.csvContent()), requestId());
  }

  @PostMapping("/imports/commit")
  public ApiResponse<ImportPreview> commitImport(
      Authentication authentication, @Valid @RequestBody ImportRequest request) {
    return ApiResponse.success(
        service.commitImport(
            CurrentIdentity.from(authentication),
            request.type(),
            request.csvContent(),
            requestId()),
        requestId());
  }

  @GetMapping("/accounts")
  public ApiResponse<PageResponse<AccountSummary>> accounts(
      @RequestParam(defaultValue = "") String query,
      @RequestParam(defaultValue = "") String status,
      @RequestParam(defaultValue = "0") @Min(0) int page,
      @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
    return ApiResponse.success(service.accounts(query, status, page, size), requestId());
  }

  @PatchMapping("/accounts/{userId}/status")
  public ApiResponse<Void> updateAccountStatus(
      Authentication authentication,
      @PathVariable UUID userId,
      @Valid @RequestBody AccountStatusRequest request) {
    service.updateAccountStatus(
        CurrentIdentity.from(authentication), userId, request.status(), requestId());
    return ApiResponse.success(null, requestId());
  }

  @GetMapping("/operation-logs")
  public ApiResponse<PageResponse<OperationLogResponse>> operationLogs(
      @RequestParam(defaultValue = "0") @Min(0) int page,
      @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
    return ApiResponse.success(service.operationLogs(page, size), requestId());
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
