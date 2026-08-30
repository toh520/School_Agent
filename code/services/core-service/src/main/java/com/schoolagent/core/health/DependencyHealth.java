package com.schoolagent.core.health;

public record DependencyHealth(String status, String version) {

  public static DependencyHealth up(String version) {
    return new DependencyHealth("UP", version);
  }

  public static DependencyHealth down() {
    return new DependencyHealth("DOWN", null);
  }
}
