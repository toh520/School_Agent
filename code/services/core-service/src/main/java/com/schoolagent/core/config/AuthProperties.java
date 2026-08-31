package com.schoolagent.core.config;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

/** Authentication lifetimes and the environment-supplied JWT signing secret. */
@Validated
@ConfigurationProperties(prefix = "school-agent.auth")
public class AuthProperties {

  @NotBlank
  @Size(min = 32)
  private String jwtSecret;

  @Min(5)
  @Max(60)
  private long accessTokenMinutes = 15;

  @Min(1)
  @Max(30)
  private long refreshTokenDays = 7;

  public String getJwtSecret() {
    return jwtSecret;
  }

  public void setJwtSecret(String jwtSecret) {
    this.jwtSecret = jwtSecret;
  }

  public long getAccessTokenMinutes() {
    return accessTokenMinutes;
  }

  public void setAccessTokenMinutes(long accessTokenMinutes) {
    this.accessTokenMinutes = accessTokenMinutes;
  }

  public long getRefreshTokenDays() {
    return refreshTokenDays;
  }

  public void setRefreshTokenDays(long refreshTokenDays) {
    this.refreshTokenDays = refreshTokenDays;
  }
}
