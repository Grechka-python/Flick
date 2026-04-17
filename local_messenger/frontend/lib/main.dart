import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme/app_theme.dart';
import 'screens/login_screen.dart';
import 'screens/chat_list_screen.dart';
import 'services/auth_service.dart';
import 'services/websocket_service.dart';

void main() {
  runApp(const LocalMessengerApp());
}

class LocalMessengerApp extends StatelessWidget {
  const LocalMessengerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => WebSocketService()),
      ],
      child: MaterialApp(
        title: 'Local Messenger',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: const LoginScreen(),
      ),
    );
  }
}
