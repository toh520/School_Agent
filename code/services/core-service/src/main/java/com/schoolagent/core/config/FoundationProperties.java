package com.schoolagent.core.config;

import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

/** Required cross-service addresses for the M01 foundation. */
@Validated
@ConfigurationProperties(prefix = "school-agent")
public class FoundationProperties {

  @NotBlank private String agentBaseUrl;

  @NotBlank private String webOrigin;

  public String getAgentBaseUrl() {
    return agentBaseUrl;
  }

  public void setAgentBaseUrl(String agentBaseUrl) {
    this.agentBaseUrl = agentBaseUrl;
  }

  public String getWebOrigin() {
    return webOrigin;
  }

  public void setWebOrigin(String webOrigin) {
    this.webOrigin = webOrigin;
  }
}
