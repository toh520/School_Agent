package com.schoolagent.core.identity;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.identity.IdentityDtos.AuditEventResponse;
import com.schoolagent.core.web.ApiResponse;
import com.schoolagent.core.web.PageResponse;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.time.Instant;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/api/v1")
public class AuditController {

  private final AuditRepository audits;

  public AuditController(AuditRepository audits) {
    this.audits = audits;
  }

  @GetMapping("/users/me/audit-events")
  public ApiResponse<PageResponse<AuditEventResponse>> myEvents(
      Authentication authentication,
      @RequestParam(required = false) String eventType,
      @RequestParam(required = false) String module,
      @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
          Instant from,
      @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
          Instant to,
      @RequestParam(defaultValue = "0") @Min(0) int page,
      @RequestParam(defaultValue = "20") @Min(1) @Max(200) int size) {
    UUID userId = CurrentIdentity.from(authentication).userId();
    return ApiResponse.success(
        audits.search(userId, eventType, module, from, to, page, size), requestId());
  }

  @GetMapping("/admin/audit-events")
  @PreAuthorize("hasRole('INFO_ADMIN')")
  public ApiResponse<PageResponse<AuditEventResponse>> adminEvents(
      @RequestParam(required = false) UUID userId,
      @RequestParam(required = false) String eventType,
      @RequestParam(required = false) String module,
      @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
          Instant from,
      @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
          Instant to,
      @RequestParam(defaultValue = "0") @Min(0) int page,
      @RequestParam(defaultValue = "20") @Min(1) @Max(200) int size) {
    return ApiResponse.success(
        audits.search(userId, eventType, module, from, to, page, size), requestId());
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
