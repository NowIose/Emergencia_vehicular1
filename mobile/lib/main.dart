import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'src/core/theme/app_theme.dart';
import 'src/features/auth/presentation/pages/login_screen.dart';

// 1. IMPORTA TU HOME REAL AQUÍ
// Verifica que la ruta sea exactamente esta:
import 'package:mobile/src/features/home/presentation/pages/home_screen.dart';
import 'src/features/messages/presentation/pages/messages_screen.dart'; // Importa la pantalla
import 'package:mobile/src/features/workshops/presentation/pages/workshops_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await dotenv.load(fileName: ".env");
  } catch (e) {
    debugPrint("Archivo .env no encontrado");
  }

  runApp(const KineticTrustApp());
}

class KineticTrustApp extends StatelessWidget {
  const KineticTrustApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenUtilInit(
      designSize: const Size(360, 690),
      minTextAdapt: true,
      splitScreenMode: true,
      builder: (context, child) {
        return MaterialApp(
          title: 'Kinetic Trust',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.lightTheme,

          home: const LoginScreen(),

          // 2. CONFIGURA LAS RUTAS
          routes: {
            '/login': (context) => const LoginScreen(),
            // Aquí Flutter usará el HomeScreen que importaste arriba
            '/home': (context) => const HomeScreen(),
            '/messages': (context) => const MessagesScreen(),
            '/workshops': (context) => const WorkshopsScreen(),
          },
        );
      },
    );
  }
}
