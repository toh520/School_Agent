package com.schoolagent.core.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/** Limits browser access to the explicitly configured local front-end origin. */
@Configuration
public class WebConfig implements WebMvcConfigurer {

  private final FoundationProperties properties;

  public WebConfig(FoundationProperties properties) {
    this.properties = properties;
  }

  @Override
  public void addCorsMappings(CorsRegistry registry) {
    registry
        .addMapping("/api/**")
        .allowedOrigins(properties.getWebOrigin())
        .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
        .allowedHeaders("Content-Type", "Authorization", RequestIdFilter.REQUEST_ID_HEADER)
        .exposedHeaders(RequestIdFilter.REQUEST_ID_HEADER);
  }
}
