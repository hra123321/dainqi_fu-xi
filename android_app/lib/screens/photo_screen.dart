import "dart:io";
import "package:flutter/material.dart";
import "package:image_picker/image_picker.dart";
import "../models/models.dart";
import "../services/api_service.dart";
import "result_screen.dart";

class PhotoScreen extends StatefulWidget {
  final AppConfig config;
  const PhotoScreen({super.key, required this.config});
  @override
  State<PhotoScreen> createState() => _PhotoScreenState();
}

class _PhotoScreenState extends State<PhotoScreen> {
  final ImagePicker _picker = ImagePicker();
  File? _imageFile;
  bool _isProcessing = false;
  String? _ocrText;
  String? _error;

  Future<void> _takePhoto(ImageSource source) async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 85,
      );
      if (photo != null) {
        setState(() {
          _imageFile = File(photo.path);
          _ocrText = null;
          _error = null;
        });
      }
    } catch (e) {
      setState(() => _error = "拍照失败: $e");
    }
  }

  Future<void> _processImage() async {
    if (_imageFile == null) return;
    setState(() => _isProcessing = true);

    try {
      if (widget.config.mode == ConnectionMode.local) {
        setState(() {
          _ocrText = "本地模式：请安装完整 App 使用本地 OCR";
          _isProcessing = false;
        });
        return;
      }

      final api = ApiService(widget.config);
      final result = await api.uploadPhoto(_imageFile!);

      setState(() {
        if (result.success && result.text.isNotEmpty) {
          _ocrText = result.text;
        } else {
          _error = result.error ?? "未识别到文字";
        }
        _isProcessing = false;
      });
    } catch (e) {
      setState(() {
        _error = "处理失败: $e";
        _isProcessing = false;
      });
    }
  }

  void _goToResult() {
    if (_ocrText == null || _ocrText!.isEmpty) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ResultScreen(
          config: widget.config,
          ocrText: _ocrText!,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text("拍照识别")),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 拍照/选图按钮
          Row(
            children: [
              Expanded(
                child: _ActionButton(
                  icon: Icons.camera_alt,
                  label: "拍照",
                  onTap: () => _takePhoto(ImageSource.camera),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _ActionButton(
                  icon: Icons.photo_library,
                  label: "从相册选择",
                  onTap: () => _takePhoto(ImageSource.gallery),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // 图片预览
          if (_imageFile != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.file(
                _imageFile!,
                height: 300,
                width: double.infinity,
                fit: BoxFit.cover,
              ),
            )
          else
            Container(
              height: 200,
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.image_outlined,
                        size: 48, color: theme.colorScheme.onSurfaceVariant),
                    const SizedBox(height: 8),
                    Text("点击上方按钮拍照或选择图片",
                        style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
                  ],
                ),
              ),
            ),

          const SizedBox(height: 16),

          // 处理按钮
          if (_imageFile != null)
            FilledButton.icon(
              onPressed: _isProcessing ? null : _processImage,
              icon: _isProcessing
                  ? const SizedBox(
                      width: 18, height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.auto_fix_high),
              label: Text(_isProcessing ? "识别中..." : "识别题目"),
            ),

          // 错误信息
          if (_error != null) ...[
            const SizedBox(height: 12),
            Card(
              color: theme.colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, color: theme.colorScheme.error),
                    const SizedBox(width: 8),
                    Expanded(child: Text(_error!)),
                  ],
                ),
              ),
            ),
          ],

          // OCR 结果
          if (_ocrText != null) ...[
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.text_snippet, size: 20),
                        const SizedBox(width: 8),
                        Text("识别结果", style: theme.textTheme.titleSmall),
                        const Spacer(),
                        Text("${_ocrText!.length} 字符",
                            style: TextStyle(
                                color: theme.colorScheme.onSurfaceVariant, fontSize: 12)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: SelectableText(_ocrText!),
                    ),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                      onPressed: _goToResult,
                      icon: const Icon(Icons.auto_stories),
                      label: const Text("开始答题"),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _ActionButton({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Theme.of(context).colorScheme.primaryContainer,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Column(
            children: [
              Icon(icon, size: 32, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 4),
              Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
          ),
        ),
      ),
    );
  }
}
