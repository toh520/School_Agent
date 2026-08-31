package com.schoolagent.core.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.schoolagent.core.config.RequestIdFilter;
import com.schoolagent.core.web.ApiResponse;
import com.schoolagent.core.web.ErrorCode;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.slf4j.MDC;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;

/** Writes authentication and authorization failures using the M01 response envelope. */
@Component
public class SecurityResponseWriter {

  private final ObjectMapper objectMapper;

  public SecurityResponseWriter(ObjectMapper objectMapper) {
    this.objectMapper = objectMapper;
  }

  public void write(HttpServletResponse response, int status, ErrorCode errorCode)
      throws IOException {
    response.setStatus(status);
    response.setCharacterEncoding(StandardCharsets.UTF_8.name());
    response.setContentType(MediaType.APPLICATION_JSON_VALUE);
    objectMapper.writeValue(
        response.getWriter(), ApiResponse.failure(errorCode, MDC.get(RequestIdFilter.MDC_KEY)));
  }
}
