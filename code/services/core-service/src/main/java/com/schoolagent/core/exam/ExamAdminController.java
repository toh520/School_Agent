package com.schoolagent.core.exam;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.exam.ExamDtos.ExamResponse;
import com.schoolagent.core.exam.ExamDtos.ExamUpsertRequest;
import com.schoolagent.core.web.ApiResponse;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** Information administrators maintain student exam schedules from the management workspace. */
@RestController
@RequestMapping("/api/v1/admin/management/exams/users/{userId}")
@PreAuthorize("hasRole('INFO_ADMIN')")
public class ExamAdminController {
  private final ExamService service;

  public ExamAdminController(ExamService service) {
    this.service = service;
  }

  @GetMapping
  public ApiResponse<List<ExamResponse>> list(@PathVariable UUID userId) {
    return ApiResponse.success(service.adminList(userId), requestId());
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public ApiResponse<ExamResponse> create(
      @PathVariable UUID userId, @Valid @RequestBody ExamUpsertRequest request) {
    return ApiResponse.success(service.adminCreate(userId, request), requestId());
  }

  @PutMapping("/{examId}")
  public ApiResponse<ExamResponse> update(
      @PathVariable UUID userId,
      @PathVariable UUID examId,
      @Valid @RequestBody ExamUpsertRequest request) {
    return ApiResponse.success(service.adminUpdate(userId, examId, request), requestId());
  }

  @DeleteMapping("/{examId}")
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void delete(@PathVariable UUID userId, @PathVariable UUID examId) {
    service.adminDelete(userId, examId);
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
