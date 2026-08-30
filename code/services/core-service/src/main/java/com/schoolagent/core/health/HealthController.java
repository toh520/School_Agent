package com.schoolagent.core.health;

import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.web.ApiResponse;
import org.slf4j.MDC;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/health")
public class HealthController {

  private final HealthService healthService;

  public HealthController(HealthService healthService) {
    this.healthService = healthService;
  }

  @GetMapping("/system")
  public ApiResponse<SystemHealth> systemHealth() {
    String requestId = MDC.get(RequestIdFilter.MDC_KEY);
    return ApiResponse.success(healthService.inspect(requestId), requestId);
  }
}
