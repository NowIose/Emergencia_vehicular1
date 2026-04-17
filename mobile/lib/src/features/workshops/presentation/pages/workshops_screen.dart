import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class WorkshopsScreen extends StatelessWidget {
  const WorkshopsScreen({super.key});

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
            filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
            child: AppBar(
              backgroundColor: AppColors.surface.withOpacity(0.7),
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
                      fontSize: 18,
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
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppColors.surfaceContainerHighest,
                      image: const DecorationImage(
                        image: NetworkImage(
                          'https://lh3.googleusercontent.com/aida-public/AB6AXuAZtXrXSgADPGDa11eYFjCPeh1sYPfcrvwQiSg1bq3UZBTig9NJGYRSKU7mYSsIqKiktLkW_vznlVBIds-Szo-ytIZ6Px1cENPBjg61bp7rgqTjtMd5LsStXc1Dtb3Ox1SmwOeK-82PdTGrtHRRhfxjhqMD-WN-b1LtzQrMBKTd-QPrJq1UJfvoPSykzq7HzPnA3sVhuxGtbKkkahQ6VjHB5Lm6rV5VfCLe6Fa_Ou8i6e8_z8fc2d6-zM13o6gy9O-Upm_T0qbcG0KR',
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
            left: 16,
            right: 16,
            bottom: 120, // accommodate bottom nav bar
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Search Input
              Container(
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerHighest.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: TextField(
                  decoration: InputDecoration(
                    hintText: 'Buscar talleres...',
                    hintStyle: TextStyle(
                      fontFamily: 'Inter',
                      color: AppColors.onSurfaceVariant.withOpacity(0.6),
                      fontSize: 16,
                    ),
                    prefixIcon: const Icon(
                      Icons.search,
                      color: AppColors.onSurfaceVariant,
                    ),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 16,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Filter Chips
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildFilterChip('Todos', isSelected: true),
                    _buildFilterChip('Cercanos'),
                    _buildFilterChip('Mejor valorados'),
                    _buildFilterChip('Especializados'),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Workshops List
              _buildWorkshopCard(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuAyrjX2g-NIU3W0bWiJHb0YqQUyx-0q9BlvIRck8EE0kH3oZnfPgYZE9s1pILcJAhSbkeUb0KykgfhsGnKNJAYKgE0TgkdvwPj_V_SQ9apHE--fet3FRs88BzM9jmdyjL4ZlMe1wz28xBOY3QphLddVVlSCwCqMaVRP-0tVG3PAlB2VnjX4uIX3kmFmCqCq4Skcu-IhutBGY-8jiKnOQmaKvrPvcqF0zq5tAT67CWFT5aXNdt_ghX9xM3oaZ9DfHvF39oEB_Ky2gTrF',
                rating: '4.9',
                title: 'MasterTech Elite',
                location: 'Calle de la Innovación 42, Madrid',
                badges: [
                  _buildBadge('BMW Specialist', AppColors.secondary),
                  _buildBadge('Hybrid', AppColors.tertiary),
                ],
              ),
              const SizedBox(height: 24),
              _buildWorkshopCard(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuDxYKwCxIbYL-AmhhKyz3GMTwD3QoPlH3TZYMvPxhGvtsTsObqm-c5pmOLxNma8cAvh8orVYO4LvDGOuzjN3iyJOgm7PRGBX7DcpkNAB07wZd3TQOXPmS2phDflWwcw9hm_QahOEqgQNt5UFhBAnFloNWJYfkT8JIJU-DzpBUISDYE_vnOZeMWAeOtA7EBVApZWUkDKeu2LOv5WfSsAgJifOVBMTWolSWju_Wg9BLvz3uAjZRu7jkmNsXynx0YEoOk4DPME0TX9qYzm',
                rating: '4.7',
                title: 'Mecánica del Futuro',
                location: 'Av. Central 128, Barcelona',
                badges: [
                  _buildBadge('Quick Service', AppColors.secondary),
                  _buildBadge('Electric', AppColors.tertiary),
                ],
              ),
              const SizedBox(height: 24),
              _buildWorkshopCard(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuC7U7MAmWLqc51rW0KAKZ_AWmnJymgitsyqIQ8KcnJreI49qSqKYSKvyycUxSMaej34CRxxURGUlU40sfW_4GMwBermQsJ-8a4yOEhW2PCZWlBGfPHKutylRIe5_09JZfpxPlp-Vqq_Oifi50PydcoS27YDuDgQAxMMggwfqm7V74EwFD3PHm7XZMpBJC6cuM1748ElOuex7y9cISJym0iMsBNsuyA9N6WKw6H3UUWX5U4pOWhM3pKGADYbY259hQrs5yEgm6OykUcR',
                rating: '4.5',
                title: 'Precision Wheels',
                location: 'Polígono Industrial Norte, Valencia',
                badges: [
                  _buildBadge('Tires', AppColors.secondary),
                  _buildBadge('Suspension', AppColors.tertiary),
                ],
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
          child: Container(
            color: Colors.white.withOpacity(0.8),
            padding: EdgeInsets.only(
              bottom: MediaQuery.of(context).padding.bottom,
            ),
            child: BottomNavigationBar(
              elevation: 0,
              backgroundColor: Colors.transparent,
              type: BottomNavigationBarType.fixed,
              currentIndex: 1, // Workshops is active
              onTap: (index) {
                if (index == 0)
                  Navigator.pushReplacementNamed(context, '/home');
                if (index == 2)
                  Navigator.pushReplacementNamed(context, '/messages');
              },
              selectedItemColor: const Color(0xFFB91C1C), // red-700
              unselectedItemColor: Colors.grey[500],
              selectedLabelStyle: const TextStyle(
                fontFamily: 'Inter',
                fontSize: 11,
                fontWeight: FontWeight.bold,
              ),
              unselectedLabelStyle: const TextStyle(
                fontFamily: 'Inter',
                fontSize: 11,
                fontWeight: FontWeight.w500,
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

  Widget _buildFilterChip(String label, {bool isSelected = false}) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      child: Material(
        color: isSelected ? AppColors.primary : AppColors.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(24),
        child: InkWell(
          onTap: () {},
          borderRadius: BorderRadius.circular(24),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              label,
              style: TextStyle(
                fontFamily: 'Inter',
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: isSelected ? AppColors.onPrimary : AppColors.onSurface,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildWorkshopCard({
    required String imageUrl,
    required String rating,
    required String title,
    required String location,
    required List<Widget> badges,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 32,
            offset: const Offset(0, 12),
            spreadRadius: -4,
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image and rating badge
          SizedBox(
            height: 192,
            width: double.infinity,
            child: Stack(
              fit: StackFit.expand,
              children: [
                Image.network(imageUrl, fit: BoxFit.cover),
                Positioned(
                  top: 12,
                  right: 12,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        color: Colors.white.withOpacity(0.9),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.star,
                              color: Colors.amber,
                              size: 14,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              rating,
                              style: const TextStyle(
                                fontFamily: 'Inter',
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                                color: AppColors.onSurface,
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
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: AppColors.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Wrap(spacing: 4, runSpacing: 4, children: badges),
                    ),
                    TextButton(
                      onPressed: () {},
                      style: TextButton.styleFrom(
                        padding: EdgeInsets.zero,
                        minimumSize: Size.zero,
                        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      child: const Text(
                        'Saber más',
                        style: TextStyle(
                          fontFamily: 'Inter',
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppColors.primary,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBadge(String text, Color baseColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: baseColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        text.toUpperCase(),
        style: TextStyle(
          fontFamily: 'Inter',
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: baseColor,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
