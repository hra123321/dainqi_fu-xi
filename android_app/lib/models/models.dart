/// 连接模式枚举
enum ConnectionMode {
  network("wifi", "WiFi 连接", "通过校园网连接电脑服务器", Icons.wifi),
  usb("usb", "USB 有线连接", "通过 USB 数据线连接电脑", Icons.cable),
  local("local", "手机本地处理", "完全在手机本地运行", Icons.phone_android);

  final String id;
  final String name;
  final String description;
  final IconData icon;
  const ConnectionMode(this.id, this.name, this.description, this.icon);
}

/// App 配置模型
class AppConfig {
  final String serverIp;
  final int port;
  final ConnectionMode mode;

  AppConfig({
    this.serverIp = "192.168.17.129",
    this.port = 8000,
    this.mode = ConnectionMode.network,
  });

  String get baseUrl => "http://$serverIp:$port";

  AppConfig copyWith({
    String? serverIp,
    int? port,
    ConnectionMode? mode,
  }) {
    return AppConfig(
      serverIp: serverIp ?? this.serverIp,
      port: port ?? this.port,
      mode: mode ?? this.mode,
    );
  }
}

/// OCR 识别结果
class OcrResult {
  final bool success;
  final String text;
  final String? error;

  OcrResult({required this.success, required this.text, this.error});

  factory OcrResult.fromJson(Map<String, dynamic> json) {
    return OcrResult(
      success: json["success"] ?? false,
      text: json["text"] ?? "",
      error: json["error"],
    );
  }
}

/// 题目数据
class Question {
  final String id;
  final String questionText;
  final String type;
  final String difficulty;

  Question({
    required this.id,
    required this.questionText,
    required this.type,
    required this.difficulty,
  });

  factory Question.fromJson(Map<String, dynamic> json) {
    return Question(
      id: json["id"] ?? "",
      questionText: json["question_text"] ?? "",
      type: json["type"] ?? "choice",
      difficulty: json["difficulty"] ?? "normal",
    );
  }
}

/// 批改结果
class GradingResult {
  final double score;
  final String conclusion;
  final String analysis;

  GradingResult({
    required this.score,
    required this.conclusion,
    required this.analysis,
  });

  factory GradingResult.fromJson(Map<String, dynamic> json) {
    return GradingResult(
      score: (json["score"] ?? 0).toDouble(),
      conclusion: json["conclusion"] ?? "未知",
      analysis: json["analysis"] ?? "",
    );
  }
}
