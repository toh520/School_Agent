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
  void validatesSingleCanteenFoodAndNormalizesValues() {
    ValidationResult result =
        validator.validate(
            ResourceType.DISH,
            Map.ofEntries(
                Map.entry("code", "dish-01"),
                Map.entry("name", "示例餐品"),
                Map.entry("price", "12.50"),
                Map.entry("category", "meat"),
                Map.entry("description", "用于智能食堂测试的餐品"),
                Map.entry("mealRole", "main"),
                Map.entry("ingredients", "鸡肉|青菜"),
                Map.entry("spiceLevel", "mild"),
                Map.entry("availabilityStatus", "available"),
                Map.entry("featured", "yes"),
                Map.entry("source", "窗口公示")),
            null,
            2);

    assertThat(result.errors()).isEmpty();
    assertThat(result.values().get("code")).isEqualTo("DISH-01");
    assertThat(result.values().get("category")).isEqualTo("MEAT");
    assertThat(result.values().get("ingredients")).isEqualTo(List.of("鸡肉", "青菜"));
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
  void validatesSimpleKnowledgeTextForRetrieval() {
    ValidationResult result =
        validator.validate(
            ResourceType.KNOWLEDGE,
            Map.of(
                "code", "NOTICE-01",
                "name", "图书馆开放通知",
                "category", "校园服务",
                "body", "图书馆开放时间以学校最新公告为准。",
                "source", "校园知识库管理"),
            null,
            4);

    assertThat(result.errors()).isEmpty();
    assertThat(result.values()).doesNotContainKey("keywords");
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
