package com.schoolagent.core.exam;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.exam.ExamDtos.ExamResponse;
import com.schoolagent.core.identity.CurrentIdentity;
import com.schoolagent.core.web.ApiResponse;
import java.util.List;
import java.util.UUID;
import org.slf4j.MDC;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** Read-only student exam schedule API. It never invokes the Agent or model service. */
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

  private UUID id(Authentication authentication) {
    return CurrentIdentity.from(authentication).userId();
  }

  private String requestId() {
    return MDC.get(RequestIdFilter.MDC_KEY);
  }
}
