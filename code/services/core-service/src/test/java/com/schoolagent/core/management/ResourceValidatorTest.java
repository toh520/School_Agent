package com.schoolagent.core.management;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class ResourceValidatorTest {

  private ManagementRepository repository;
  private ResourceValidator validator;

  @BeforeEach
  void setUp() {
    repository = mock(ManagementRepository.class);
    validator = new ResourceValidator(repository);
  }

  @Test
  void validatesDishReferencesAndNormalizesValues() {
    when(repository.existsCode(ResourceType.STALL, "STALL-01", null)).thenReturn(true);
    when(repository.existsCode(ResourceType.INGREDIENT, "ING-01", null)).thenReturn(true);

    ValidationResult result =
        validator.validate(
            ResourceType.DISH,
            Map.of(
                "code", "dish-01",
                "name", "示例菜品",
                "stallCode", "stall-01",
                "price", "12.50",
                "ingredientCodes", "ing-01",
                "availabilityStatus", "available",
                "source", "窗口公示"),
            null,
            2);

    assertThat(result.errors()).isEmpty();
    assertThat(result.values().get("code")).isEqualTo("DISH-01");
    assertThat(result.values().get("stallCode")).isEqualTo("STALL-01");
    assertThat(result.values().get("ingredientCodes")).isEqualTo(List.of("ing-01"));
  }

  @Test
  void rejectsHoldingCountThatExceedsTotal() {
    when(repository.existsCode(ResourceType.BOOK, "BOOK-01", null)).thenReturn(true);

    ValidationResult result =
        validator.validate(
            ResourceType.HOLDING,
            Map.of(
                "code", "HOLD-01",
                "name", "示例馆藏",
                "bookCode", "BOOK-01",
                "callNumber", "TP3/1",
                "location", "主馆二层",
                "totalCount", "1",
                "availableCount", "2",
                "availabilityStatus", "AVAILABLE",
                "source", "馆藏系统"),
            null,
            3);

    assertThat(result.errors())
        .anyMatch(
            error -> error.field().equals("availableCount") && error.message().contains("不能超过总册数"));
  }

  @Test
  void validatesSimpleAnnouncementTextForFutureRetrieval() {
    ValidationResult result =
        validator.validate(
            ResourceType.KNOWLEDGE,
            Map.of(
                "code", "NOTICE-01",
                "name", "图书馆开放通知",
                "category", "校园服务",
                "keywords", "图书馆|开放时间|自习",
                "body", "图书馆开放时间以学校最新公告为准。",
                "source", "学校公开公告"),
            null,
            4);

    assertThat(result.errors()).isEmpty();
    assertThat(result.values().get("keywords")).isEqualTo(List.of("图书馆", "开放时间", "自习"));
    assertThat(result.completeness()).isEqualTo(100);
  }

  @Test
  void blocksSensitiveSystemConfiguration() {
    ValidationResult result =
        validator.validate(
            ResourceType.SYSTEM_CONFIG,
            Map.of(
                "code", "API-SECRET",
                "name", "接口密钥",
                "configValue", "must-not-be-stored",
                "source", "错误示例"),
            null,
            5);

    assertThat(result.errors()).anyMatch(error -> error.field().equals("code"));
  }
}
