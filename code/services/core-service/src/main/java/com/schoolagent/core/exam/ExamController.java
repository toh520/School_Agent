package com.schoolagent.core.exam;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.exam.ExamDtos.ExamResponse;
import com.schoolagent.core.exam.ExamDtos.ExamUpsertRequest;
import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.web.ApiResponse;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** Student exam schedule API. It never invokes the Agent or model service. */
@RestController
@RequestMapping("/api/v1/exams")
@PreAuthorize("hasRole('STUDENT')")
public class ExamController {
  private final ExamService service;

  public ExamController(ExamService service) {
    this.service = service;
  }

  @GetMapping
  public ApiResponse<List<ExamResponse>> list(Authentication authentication) {
    return ApiResponse.success(service.list(id(authentication)), requestId());
  }

  @GetMapping("/next")
  public ApiResponse<ExamResponse> next(Authentication authentication) {
    return ApiResponse.success(service.next(id(authentication)), requestId());
  }

  @PostMapping
  @ResponseStatus(HttpStatus.CREATED)
  public ApiResponse<ExamResponse> create(
      Authentication authentication, @Valid @RequestBody ExamUpsertRequest request) {
    return ApiResponse.success(service.create(id(authentication), request), requestId());
  }

  @PutMapping("/{examId}")
  public ApiResponse<ExamResponse> update(
      Authentication authentication,
      @PathVariable UUID examId,
      @Valid @RequestBody ExamUpsertRequest request) {
    return ApiResponse.success(service.update(id(authentication), examId, request), requestId());
  }

  @DeleteMapping("/{examId}")
  @ResponseStatus(HttpStatus.NO_CONTENT)
  public void delete(Authentication authentication, @PathVariable UUID examId) {
    service.delete(id(authentication), examId);
  }

  private UUID id(Authentication authentication) {
    return CurrentIdentity.from(authentication).userId();
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
