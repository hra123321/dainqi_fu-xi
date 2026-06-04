import "dart:convert";
import "dart:io";
import "package:http/http.dart" as http;
import "../models/models.dart";

class ApiService {
  final AppConfig config;
  ApiService(this.config);
  String get _base => config.baseUrl;

  Future<bool> checkConnection() async {
    try {
      final resp = await http
          .get(Uri.parse("$_base/api/health"))
          .timeout(const Duration(seconds: 3));
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<OcrResult> uploadPhoto(File imageFile) async {
    try {
      final request = http.MultipartRequest(
        "POST",
        Uri.parse("$_base/api/mobile/photo/upload"),
      );
      request.files.add(
        await http.MultipartFile.fromPath("file", imageFile.path),
      );
      final streamedResp = await request.send().timeout(
        const Duration(seconds: 30),
      );
      final resp = await http.Response.fromStream(streamedResp);
      if (resp.statusCode == 200) {
        return OcrResult.fromJson(json.decode(resp.body));
      }
      return OcrResult(success: false, text: "", error: "HTTP ${resp.statusCode}");
    } catch (e) {
      return OcrResult(success: false, text: "", error: e.toString());
    }
  }

  Future<List<Question>> generateQuestions({
    required String knowledgePoint,
    String difficulty = "normal",
    int count = 3,
  }) async {
    final resp = await http
        .post(
          Uri.parse("$_base/api/exam/generate"),
          headers: {"Content-Type": "application/json"},
          body: json.encode({
            "knowledge_point": knowledgePoint,
            "difficulty": difficulty,
            "count": count,
          }),
        )
        .timeout(const Duration(seconds: 60));
    if (resp.statusCode == 200) {
      final data = json.decode(resp.body);
      return (data["questions"] as List)
          .map((q) => Question.fromJson(q))
          .toList();
    }
    throw Exception("Failed: ${resp.statusCode}");
  }

  Future<GradingResult> submitAnswer({
    required String questionId,
    required String questionType,
    required String question,
    required String studentAnswer,
    String? correctAnswer,
    String? referenceAnswer,
    String knowledgeContext = "",
  }) async {
    final resp = await http
        .post(
          Uri.parse("$_base/api/exam/submit"),
          headers: {"Content-Type": "application/json"},
          body: json.encode({
            "question_id": questionId,
            "question_type": questionType,
            "question": question,
            "student_answer": studentAnswer,
            "correct_answer": correctAnswer,
            "reference_answer": referenceAnswer,
            "knowledge_context": knowledgeContext,
          }),
        )
        .timeout(const Duration(seconds: 60));
    if (resp.statusCode == 200) {
      return GradingResult.fromJson(json.decode(resp.body));
    }
    throw Exception("Failed: ${resp.statusCode}");
  }

  Future<Map<String, dynamic>> getNetworkInfo() async {
    final resp = await http
        .get(Uri.parse("$_base/api/mobile/network-info"))
        .timeout(const Duration(seconds: 5));
    if (resp.statusCode == 200) return json.decode(resp.body);
    return {};
  }
}
