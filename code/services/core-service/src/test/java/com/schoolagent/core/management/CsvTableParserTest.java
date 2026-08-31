package com.schoolagent.core.management;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class CsvTableParserTest {

  private final CsvTableParser parser = new CsvTableParser();

  @Test
  void parsesQuotedCommaAndEscapedQuote() {
    List<Map<String, String>> rows =
        parser.parse("code,name,source\nBOOK-01,\"书名, 第一版\",\"图书馆\"\"公开目录\"\"\"\n");

    assertThat(rows).hasSize(1);
    assertThat(rows.getFirst().get("name")).isEqualTo("书名, 第一版");
    assertThat(rows.getFirst().get("source")).isEqualTo("图书馆\"公开目录\"");
  }

  @Test
  void reportsThePhysicalRowWithWrongColumnCount() {
    assertThatThrownBy(() -> parser.parse("code,name\nONE\n"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("row 2");
  }
}
