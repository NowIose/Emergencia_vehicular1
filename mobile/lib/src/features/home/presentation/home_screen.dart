import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      extendBodyBehindAppBar: true,
      extendBody: true,
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(kToolbarHeight),
        child: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: AppBar(
              backgroundColor: Colors.white.withOpacity(0.7),
              elevation: 0,
              scrolledUnderElevation: 0,
              title: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.menu, color: Colors.black54),
                    onPressed: () {},
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Kinetic Trust',
                    style: TextStyle(
                      fontFamily: 'Manrope',
                      fontWeight: FontWeight.bold,
                      fontSize: 20,
                      color: Colors.black87,
                      letterSpacing: -0.5,
                    ),
                  ),
                ],
              ),
              titleSpacing: 0,
              actions: [
                Padding(
                  padding: const EdgeInsets.only(right: 16.0),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.primary.withOpacity(0.1),
                        width: 2,
                      ),
                      color: AppColors.surfaceContainerHigh,
                      image: const DecorationImage(
                        image: NetworkImage(
                          'https://lh3.googleusercontent.com/aida-public/AB6AXuD0g_1uKAzUilYwoWYgF_GvqLpvHRQYoAreHbWfRipMUU58B33fNMOzN6S78OZjL20RV28Ne_WOaVqGcaxSNGTk7Yggj2Pz0dmSFEC0UgM4gihN_lItcmKH8jLCXVCLAvpQyPjra_AqjjLrHXvsuX7VOHrJxEp4MFSHave1uzZfwRG26r5mVtA32cqiRQ7bh0SToMBj5wMdOxpWvlFl0g73wH_4XSZBdotG63PRISs4ropI0nQpy_hSdBYG4A5oYrx-XaZIxQCCOTgx',
                        ),
                        fit: BoxFit.cover,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      body: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: EdgeInsets.only(
            top: MediaQuery.of(context).padding.top + kToolbarHeight + 16,
            left: 20,
            right: 20,
            bottom: 100, // accommodate bottom nav bar
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Hero
              const Text(
                'Hola, Juan',
                style: TextStyle(
                  fontFamily: 'Manrope',
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: AppColors.onSurface,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                '¿En qué podemos ayudarte con tu vehículo hoy?',
                style: TextStyle(
                  fontFamily: 'Inter',
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: AppColors.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 32),

              // Search Bar
              Container(
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerHighest.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: TextField(
                  decoration: InputDecoration(
                    hintText: 'Buscar taller o servicio',
                    hintStyle: const TextStyle(
                      fontFamily: 'Inter',
                      color: AppColors.outline,
                    ),
                    prefixIcon: const Icon(
                      Icons.search,
                      color: AppColors.outline,
                    ),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 16,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 32),

              // Quick Actions Bento
              Row(
                children: [
                  // CARD DE MENSAJERÍA
                  Expanded(
                    child: GestureDetector(
                      onTap: () => Navigator.pushNamed(context, '/messages'),
                      child: _buildBentoCard(
                        icon: Icons.chat,
                        iconColor: AppColors.secondary,
                        iconBgColor: AppColors.secondary.withOpacity(0.2),
                        title: 'Mensajería',
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),

                  // CARD DE TALLERES (ESTE ES EL QUE EDITAMOS)
                  Expanded(
                    child: GestureDetector(
                      onTap: () => Navigator.pushNamed(
                        context,
                        '/workshops',
                      ), // <--- NAVEGACIÓN AQUÍ
                      child: _buildBentoCard(
                        icon: Icons.home_repair_service,
                        iconColor: AppColors.primary,
                        iconBgColor: AppColors.primary.withOpacity(0.1),
                        title: 'Ver Talleres',
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // Featured Workshops
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Talleres Destacados',
                    style: TextStyle(
                      fontFamily: 'Manrope',
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppColors.onSurface,
                    ),
                  ),
                  TextButton(
                    onPressed: () {},
                    child: const Text(
                      'Ver todos',
                      style: TextStyle(
                        fontFamily: 'Inter',
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              _buildWorkshopCard(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuDPC93jMkMnVC9L8gZuyfOaFiF3DD6B7uwyT-oyW5dYLr3oMRXtWL5SIf6BbSCE6ac5wPzKTHetj_A568xQmHwzEKKH4C7_zatMK9tPaYJlFVqzeYHDg3hoA3QvIN8IYJ92ZtR8nHqSXE59Wi-Tc87Dp0UWwRVQGndxPp1fATFNgInMxLHEaThCtg0HIuCCf4XXnlmGICBSKL9aGQl2eADL78tq_0BXCix--E4uRuBliTtQfLH-g7dx_P2ER4oKJ10L72ljDmXYfSSR',
                title: 'Taller Central Pro',
                location: 'Madrid, Centro',
                rating: '4.8',
              ),
              const SizedBox(height: 24),
              _buildWorkshopCard(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuCpwUodNfv7vtoedN86FjpAREOGn6c64Ya35SWCIBp3QqaxsakTWFLPGIwrHElLxydNGh2vnKaZpd0lgCxEArsMWdT3IUR-zL3NTTKQ7bnfzAypaWZv23PqqPb6lp_8JAnqVQDOlgXo4-EvYq7s9B88iZhZbvk8hYrxdlb4OWAeENaDHKuin44u0Dzr9Iw0K3JppodJvz_lSb4hU2HeP29_Z27K9pn6EsfSo5uK2EtXj8mNawUNeSOUcCmeoMwo9AU7dofci0xr4E-3',
                title: 'Mecánica Avanzada',
                location: 'Barcelona, Diagonal',
                rating: '4.9',
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: Padding(
        padding: const EdgeInsets.only(bottom: 56.0),
        child: FloatingActionButton(
          onPressed: () {},
          backgroundColor: AppColors.primary,
          foregroundColor: AppColors.onPrimary,
          elevation: 4,
          shape: const CircleBorder(),
          child: const Icon(Icons.add),
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      bottomNavigationBar: ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            color: Colors.white.withOpacity(0.8),
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).padding.bottom,
            ),
            child: BottomNavigationBar(
              elevation: 0,
              backgroundColor: Colors.transparent,
              type: BottomNavigationBarType.fixed,
              selectedItemColor: const Color(0xFFB91C1C), // red-700 approx
              unselectedItemColor: Colors.grey[500],
              currentIndex: 0, // <--- 0 porque es la primera pantalla
              onTap: (index) {
                if (index == 1)
                  Navigator.pushReplacementNamed(context, '/workshops');
                if (index == 2)
                  Navigator.pushReplacementNamed(context, '/messages');
              },
              selectedLabelStyle: const TextStyle(
                fontFamily: 'Inter',
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 0.5,
              ),
              unselectedLabelStyle: const TextStyle(
                fontFamily: 'Inter',
                fontSize: 11,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5,
              ),
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.emergency_share),
                  label: 'Emergency',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.car_repair),
                  label: 'Workshops',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.chat_bubble),
                  label: 'Messages',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.person),
                  label: 'Profile',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBentoCard({
    required IconData icon,
    required Color iconColor,
    required Color iconBgColor,
    required String title,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.transparent),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.02),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: iconBgColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: iconColor),
          ),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(
              fontFamily: 'Manrope',
              fontWeight: FontWeight.w600,
              fontSize: 16,
              color: AppColors.onSurface,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWorkshopCard({
    required String imageUrl,
    required String title,
    required String location,
    required String rating,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image and badge
          SizedBox(
            height: 180,
            width: double.infinity,
            child: Stack(
              fit: StackFit.expand,
              children: [
                Image.network(imageUrl, fit: BoxFit.cover),
                Positioned(
                  top: 16,
                  right: 16,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(20),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        color: Colors.white.withOpacity(0.75),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.star,
                              color: Colors.amber,
                              size: 16,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              rating,
                              style: const TextStyle(
                                fontFamily: 'Inter',
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                                color: Colors.black87,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Content
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontFamily: 'Manrope',
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                    color: AppColors.onSurface,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(
                      Icons.location_on,
                      size: 14,
                      color: AppColors.onSurfaceVariant,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      location,
                      style: const TextStyle(
                        fontFamily: 'Inter',
                        fontSize: 14,
                        color: AppColors.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(
                        0xFFD32F2F,
                      ), // primary-container
                      foregroundColor: const Color(
                        0xFFFFF2F0,
                      ), // on-primary-container
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text(
                      'Saber más',
                      style: TextStyle(
                        fontFamily: 'Inter',
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
