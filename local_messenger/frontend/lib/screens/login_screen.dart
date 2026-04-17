import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../services/auth_service.dart';
import 'chat_list_screen.dart';
import 'register_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    final authService = Provider.of<AuthService>(context, listen: false);
    final success = await authService.login(
      username: _usernameController.text.trim(),
      password: _passwordController.text,
    );

    if (success && mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const ChatListScreen()),
      );
    } else if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Неверный логин или пароль'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppTheme.backgroundGradient),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Логотип
                    Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        color: AppTheme.accentOrange,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Icon(
                        Icons.message_rounded,
                        size: 60,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 32),
                    
                    // Заголовок
                    const Text(
                      'Local Messenger',
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textWhite,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Вход в систему',
                      style: TextStyle(
                        fontSize: 16,
                        color: AppTheme.textLightGray,
                      ),
                    ),
                    const SizedBox(height: 48),
                    
                    // Поле username
                    TextFormField(
                      controller: _usernameController,
                      style: const TextStyle(color: AppTheme.textWhite),
                      decoration: InputDecoration(
                        labelText: 'Имя пользователя',
                        labelStyle: const TextStyle(color: AppTheme.textLightGray),
                        prefixIcon: const Icon(Icons.person, color: AppTheme.accentOrange),
                        filled: true,
                        fillColor: AppTheme.messageBubbleSender,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(25),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Введите имя пользователя';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Поле password
                    TextFormField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      style: const TextStyle(color: AppTheme.textWhite),
                      decoration: InputDecoration(
                        labelText: 'Пароль',
                        labelStyle: const TextStyle(color: AppTheme.textLightGray),
                        prefixIcon: const Icon(Icons.lock, color: AppTheme.accentOrange),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword ? Icons.visibility_off : Icons.visibility,
                            color: AppTheme.accentOrange,
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                        filled: true,
                        fillColor: AppTheme.messageBubbleSender,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(25),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Введите пароль';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 32),
                    
                    // Кнопка входа
                    Consumer<AuthService>(
                      builder: (context, auth, _) {
                        return SizedBox(
                          width: double.infinity,
                          height: 50,
                          child: ElevatedButton(
                            onPressed: auth.isLoading ? null : _login,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.accentOrange,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(25),
                              ),
                            ),
                            child: auth.isLoading
                                ? const CircularProgressIndicator(color: Colors.white)
                                : const Text(
                                    'Войти',
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white,
                                    ),
                                  ),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 16),
                    
                    // Кнопка регистрации
                    TextButton(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const RegisterScreen()),
                        );
                      },
                      child: const Text(
                        'Нет аккаунта? Зарегистрироваться',
                        style: TextStyle(color: AppTheme.textLightGray),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
