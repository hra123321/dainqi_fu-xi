import "package:flutter/material.dart";
import "../models/models.dart";
import "../services/api_service.dart";

class ResultScreen extends StatefulWidget {
  final AppConfig config;
  final String ocrText;
  const ResultScreen({super.key, required this.config, required this.ocrText});
  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  final List<Question> _questions = [];
  final Map<String, TextEditingController> _answers = {};
  final List<GradingResult?> _results = [];
  bool _isLoading = false;
  bool _isSubmitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  @override
  void dispose() {
    for (final c in _answers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _loadQuestions() async {
    setState(() => _isLoading = true);
    try {
      final api = ApiService(widget.config);
      final questions = await api.generateQuestions(
        knowledgePoint: widget.ocrText.length > 200
            ? widget.ocrText.substring(0, 200)
            : widget.ocrText,
        difficulty: "normal",
        count: 3,
      );
      setState(() {
        _questions.addAll(questions);
        for (final q in questions) {
          _answers[q.id] = TextEditingController();
          _results.add(null);
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = "出题失败: $e";
        _isLoading = false;
      });
    }
  }

  Future<void> _submitAll() async {
    setState(() => _isSubmitting = true);
    final api = ApiService(widget.config);
    bool hasEmpty = false;

    for (final q in _questions) {
      if (_answers[q.id]!.text.trim().isEmpty) {
        hasEmpty = true;
        break;
      }
    }

    if (hasEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("请回答所有题目")),
      );
      setState(() => _isSubmitting = false);
      return;
    }

    for (int i = 0; i < _questions.length; i++) {
      final q = _questions[i];
      try {
        final result = await api.submitAnswer(
          questionId: q.id,
          questionType: q.type,
          question: q.questionText,
          studentAnswer: _answers[q.id]!.text,
        );
        setState(() => _results[i] = result);
      } catch (e) {
        setState(() {
          _results[i] = GradingResult(
            score: 0, conclusion: "错误", analysis: "提交失败: $e",
          );
        });
      }
    }
    setState(() => _isSubmitting = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text("答题")),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
                        const SizedBox(height: 16),
                        Text(_error!, textAlign: TextAlign.center),
                        const SizedBox(height: 16),
                        FilledButton(onPressed: _loadQuestions, child: const Text("重试")),
                      ],
                    ),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    ..._questions.asMap().entries.map((entry) {
                      final i = entry.key;
                      final q = entry.value;
                      final result = _results.length > i ? _results[i] : null;
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  CircleAvatar(
                                    radius: 12,
                                    backgroundColor: theme.colorScheme.primary,
                                    child: Text("${i + 1}",
                                        style: const TextStyle(
                                            color: Colors.white, fontSize: 12)),
                                  ),
                                  const SizedBox(width: 8),
                                  Text("第 ${i + 1} 题",
                                      style: theme.textTheme.titleSmall),
                                  const Spacer(),
                                  if (result != null)
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 8, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: result.conclusion == "正确"
                                            ? Colors.green.shade50
                                            : Colors.red.shade50,
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Text(
                                        result.conclusion,
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: result.conclusion == "正确"
                                              ? Colors.green
                                              : Colors.red,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(q.questionText),
                              const SizedBox(height: 8),
                              TextField(
                                controller: _answers[q.id],
                                decoration: InputDecoration(
                                  hintText: "输入你的答案",
                                  border: const OutlineInputBorder(),
                                  enabled: result == null,
                                ),
                                maxLines: 3,
                              ),
                              if (result != null) ...[
                                const SizedBox(height: 8),
                                Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: result.conclusion == "正确"
                                        ? Colors.green.shade50
                                        : Colors.red.shade50,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text("得分: ${result.score.toInt()}",
                                          style: TextStyle(
                                            fontWeight: FontWeight.w600,
                                            color: result.conclusion == "正确"
                                                ? Colors.green
                                                : Colors.red,
                                          )),
                                      const SizedBox(height: 4),
                                      Text(result.analysis,
                                          style: const TextStyle(fontSize: 13)),
                                    ],
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      );
                    }),
                    const SizedBox(height: 16),
                    if (_results.every((r) => r != null))
                      Card(
                        color: theme.colorScheme.primaryContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Center(
                            child: Text(
                              "总分: ${_results.fold<int>(0, (sum, r) => sum + (r?.score ?? 0).toInt())} / ${_questions.length * 100}",
                              style: theme.textTheme.titleLarge,
                            ),
                          ),
                        ),
                      ),
                    const SizedBox(height: 80),
                  ],
                ),
      bottomNavigationBar: _questions.isNotEmpty && !_isLoading
          ? SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: FilledButton.icon(
                  onPressed: _isSubmitting ? null : _submitAll,
                  icon: _isSubmitting
                      ? const SizedBox(
                          width: 18, height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Icon(Icons.check_circle),
                  label: Text(_isSubmitting ? "提交中..." : "提交全部答案"),
                ),
              ),
            )
          : null,
    );
  }
}
