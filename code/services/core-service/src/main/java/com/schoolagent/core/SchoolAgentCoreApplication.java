package com.schoolagent.core;

import com.schoolagent.core.config.RequiredEnvironment;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class SchoolAgentCoreApplication {

  public static void main(String[] args) {
    RequiredEnvironment.validate(System.getenv());
    SpringApplication.run(SchoolAgentCoreApplication.class, args);
  }
}
