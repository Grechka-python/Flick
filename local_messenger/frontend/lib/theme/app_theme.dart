import 'package:flutter/material.dart';

class AppTheme {
  // Основные цвета согласно требованиям
  static const Color primaryBlue = Color(0xFF0A2F6C);      // Глубокий синий
  static const Color accentOrange = Color(0xFFFF8C42);     // Яркий оранжевый
  static const Color sidebarBlue = Color(0xFF0F2A4A);      // Тёмно-синий для боковой панели
  static const Color messageBubbleSender = Color(0xFF0E3B5C); // Пузырь отправителя
  static const Color messageBubbleReceiver = Color(0xFF1C2E40); // Пузырь собеседника
  static const Color headerGradientStart = Color(0xFF0A2F6C);
  static const Color headerGradientEnd = Color(0xFF1E4A7A);
  
  // Текст
  static const Color textWhite = Colors.white;
  static const Color textLightGray = Color(0xFFCCCCCC);
  
  // Градиент фона
  static const LinearGradient backgroundGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [
      Color(0xFF0A2F6C),
      Color(0xFF051530),
      Color(0xFF000000),
    ],
  );
  
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primaryColor: primaryBlue,
      scaffoldBackgroundColor: const Color(0xFF051530),
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryBlue,
        foregroundColor: textWhite,
        elevation: 0,
      ),
      colorScheme: const ColorScheme.dark(
        primary: accentOrange,
        secondary: accentOrange,
        surface: sidebarBlue,
        background: Color(0xFF051530),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: messageBubbleSender,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(25),
          borderSide: BorderSide.none,
        ),
        hintStyle: const TextStyle(color: textLightGray),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accentOrange,
          foregroundColor: textWhite,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(25),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: textWhite,
        ),
      ),
      iconTheme: const IconThemeData(
        color: textWhite,
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: accentOrange,
        foregroundColor: textWhite,
      ),
    );
  }
}
