import "package:flutter/material.dart";
import "../models/models.dart";
import "../services/api_service.dart";
import "photo_screen.dart";

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  ConnectionMode _selectedMode = ConnectionMode.network;
  final TextEditingController _ipController = TextEditingController(text: "192.168.17.129");
  bool _isConnected = false;
  bool _isChecking = false;

  @override
  void dispose() {
    _ipController.dispose();
    super.dispose();
  }

  void _onSelectMode(ConnectionMode mode) {
    setState(() => _selectedMode = mode);
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    if (_selectedMode == ConnectionMode.local) {
      setState(() => _isConnected = true);
      return;
    }
    setState(() => _isChecking = true);
    final config = AppConfig(serverIp: _ipController.text, mode: _selectedMode);
    final api = ApiService(config);
    final ok = await api.checkConnection();
    setState(() {
      _isConnected = ok;
      _isChecking = false;
    });
  }

  void _openCamera() {
    final config = AppConfig(
      serverIp: _ipController.text,
      mode: _selectedMode,
    );
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => PhotoScreen(config: config),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text("电气复习助手"),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(_isConnected ? Icons.cloud_done : Icons.cloud_off),
            onPressed: _checkConnection,
            tooltip: "检查连接",
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 连接模式卡片
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("连接模式", style: theme.textTheme.titleMedium),
                  const SizedBox(height: 12),
                  ...ConnectionMode.values.map((mode) => _ModeTile(
                    mode: mode,
                    isSelected: _selectedMode == mode,
                    onTap: () => _onSelectMode(mode),
                  )),
                  if (_selectedMode != ConnectionMode.local) ...[
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _ipController,
                            decoration: const InputDecoration(
                              labelText: "服务器 IP",
                              border: OutlineInputBorder(),
                              prefixIcon: Icon(Icons.computer),
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          icon: _isChecking
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.refresh),
                          onPressed: _checkConnection,
                        ),
                      ],
                    ),
                  ],
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(
                        _isConnected ? Icons.check_circle : Icons.cancel,
                        color: _isConnected ? Colors.green : Colors.grey,
                        size: 16,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _isConnected
                            ? _selectedMode == ConnectionMode.local
                                ? "本地模式"
                                : "已连接到服务器"
                            : "未连接",
                        style: TextStyle(
                          color: _isConnected ? Colors.green : Colors.grey,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // 拍照按钮
          Card(
            child: InkWell(
              onTap: _isConnected ? _openCamera : null,
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Icon(
                      Icons.camera_alt_rounded,
                      size: 64,
                      color: _isConnected ? theme.colorScheme.primary : Colors.grey,
                    ),
                    const SizedBox(height: 12),
                    Text("拍照上传题目", style: theme.textTheme.titleMedium),
                    const SizedBox(height: 4),
                    Text(
                      _isConnected ? "点击拍照，AI 自动识别" : "请先连接服务器",
                      style: TextStyle(color: theme.colorScheme.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 16),

          // 快捷操作
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("快捷功能", style: theme.textTheme.titleMedium),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _ActionChip(
                          icon: Icons.history,
                          label: "历史记录",
                          onTap: () {},
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: _ActionChip(
                          icon: Icons.settings,
                          label: "设置",
                          onTap: () {},
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: _ActionChip(
                          icon: Icons.help_outline,
                          label: "使用说明",
                          onTap: () => _showHelp(context),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showHelp(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text("使用说明"),
        content: const Text(
          "1. 选择连接模式\n"
          "   - WiFi: 手机和电脑连同一个校园网\n"
          "   - USB: 用数据线连接电脑\n"
          "   - 本地: 手机独立运行\n\n"
          "2. 输入电脑 IP 地址\n"
          "   - 电脑使用 ipconfig 查看\n\n"
          "3. 拍照上传题目\n"
          "   - AI 自动识别文字\n"
          "   - 自动出题和批改\n\n"
          "4. 查看批改结果",
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("知道了"),
          ),
        ],
      ),
    );
  }
}

class _ModeTile extends StatelessWidget {
  final ConnectionMode mode;
  final bool isSelected;
  final VoidCallback onTap;

  const _ModeTile({required this.mode, required this.isSelected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: isSelected
            ? theme.colorScheme.primaryContainer
            : theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Icon(mode.icon, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(mode.name, style: const TextStyle(fontWeight: FontWeight.w600)),
                      Text(mode.description,
                          style: TextStyle(
                              fontSize: 12, color: theme.colorScheme.onSurfaceVariant)),
                    ],
                  ),
                ),
                Icon(
                  isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
                  color: isSelected ? theme.colorScheme.primary : null,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ActionChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _ActionChip({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Theme.of(context).colorScheme.surfaceContainerHighest,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Column(
            children: [
              Icon(icon, color: Theme.of(context).colorScheme.primary),
              const SizedBox(height: 4),
              Text(label, style: const TextStyle(fontSize: 12)),
            ],
          ),
        ),
      ),
    );
  }
}
