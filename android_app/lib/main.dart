import "package:flutter/material.dart";
import "screens/home_screen.dart";
import "screens/photo_screen.dart";
import "screens/result_screen.dart";
import "services/api_service.dart";

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ExamApp());
}

class ExamApp extends StatelessWidget {
  const ExamApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "电气复习助手",
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.system,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF1A73E8),
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF1A73E8),
        brightness: Brightness.dark,
      ),
      home: const HomeScreen(),
    );
  }
}
