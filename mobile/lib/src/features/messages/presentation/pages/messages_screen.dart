import 'dart:ui';
import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class MessagesScreen extends StatelessWidget {
  const MessagesScreen({super.key});

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
                      fontSize: 18, // Tailwind text-lg
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
                    width: 32, // w-8 h-8
                    height: 32,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.outlineVariant.withOpacity(0.15),
                      ),
                      image: const DecorationImage(
                        image: NetworkImage(
                          'https://lh3.googleusercontent.com/aida-public/AB6AXuDBB3zufS6SMd8cLMLPNnAKYHEEeY5FXFYivIjxbVT6GjxwnLjJzouZqmlDUYjuF0Z0k4pKDL7iTfOI5-tWRbBDz0vQ4DDx1IhU43ofvfAfl2Fason99TU2z4e9bll0omp6-Q0Mog6Xa1ZFJZM8OcVimm6J01aJeDiOYfFdITjPFnUxzq4x7sSrGuB1p1JFID8cIcHov6usPmqi_m-DnV1BS5AJlhbdHqpYAiCE6IFvzlzk_xp9NtVDFgPElm_DacDp1p86dFFqVfnJ',
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
              // Header Section
              const Text(
                'Messages',
                style: TextStyle(
                  fontFamily: 'Manrope',
                  fontSize: 28, // text-3xl approx
                  fontWeight: FontWeight.bold,
                  color: AppColors.onSurface,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 24),

              // Search Input
              Container(
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: TextField(
                  decoration: InputDecoration(
                    hintText: 'Search workshops or mechanics...',
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
              const SizedBox(height: 32),

              // Pinned / Active Urgent Section
              _buildActiveRequestCard(),
              const SizedBox(height: 32),

              // Chat List Section
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                margin: const EdgeInsets.only(bottom: 16),
                child: Text(
                  'RECENT CONVERSATIONS',
                  style: TextStyle(
                    fontFamily: 'Inter',
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppColors.onSurfaceVariant.withOpacity(0.7),
                    letterSpacing: 1.5,
                  ),
                ),
              ),

              _buildChatItem(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuDq0Wz75ePBRWYZ5DSI3PeatxpcVI4GPZALN9GprtI7aS09qp_ZXWMkBJNDtrTCJrn4eKlmwKwCKJp0dosbwRUStGmF7mB-38_n_qSQUUCS9hSARqUi6kjKBcfzdZY5cm3N_MQA9hKeRawWsEcpZZHDlt5yInGjWUBMhOGoR3hmujpCDIXkhtVy7GHpfNH1i-xQ6thcr87dJgByx04X1yAIJbq6ggEzE-pLvmPGSleXWLudBWxe-h0t2IV4g_vw7GzcRxCH4crYWTCT',
                name: 'Velocity Performance Lab',
                time: '10:45 AM',
                message:
                    'The diagnostic report is ready for your Tesla Model S. We found a small...',
                isOnline: true,
              ),
              _buildChatItem(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuAo96Sfx8ov4bLy2_T_LtbfRNx7Ho0KN9djPqQn9GlyshM_84ywZ8KxJT59x2jRj8Un-5dP_nV_kNvj5_55-pezeVTw-wy026PQOz9yQqzPkAxMr9N46OOTLJlz8t0CmHDxaMzj_FhDpjT2gJP3woUrt0BleZk1fkOdojZ6GgtXUzk0Ry6vmSo9BEwGSPIx8kR5rq_il8l6cG21AKE9TxvQKpBqtTIiGhbes1saP2koJI-YwQ5Yx-tIl5NkBIqeuiN-xO5vql1dmFjy',
                name: 'Master Tech European',
                time: 'Yesterday',
                message: 'You: That sounds perfect, see you at 9:00 AM.',
                isOnline: false,
              ),
              _buildChatItem(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuAREGDzSSM5AjkXy0m21u7M17jqBLP5oYKPW98FnlfdBCyzOeCm-tQl9dkHJuU0Ufj8SPlkqlB38-Spv5snr_hi-bGOdaJ3TvjfixvzbDOZNxIE1jTOW3LSRf1ddgLwSFwbPiOsTVaaumRkVWShwIPr2tAgd_6ccMAKZJln3EfGYB4acefC9M9-5rF7vs4MPBwVa-iahuPcyfHXuTq-izuJ3_6iFvdTW642lJ-XFPQDC77WPVHsew7fTkuQqu9GLPm1TOBRYy1xyKkn',
                name: 'Mobile Fix: Marcus',
                time: 'Tuesday',
                message: 'The battery replacement is complete. Safe travels!',
                isOnline: false,
              ),
              _buildChatItem(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuD54B7ULDNIWGMr7TmovO7O_LuS1i26NtKWuVzVXFX0v72FpA3jHLFuP-nKANmFfpzH8sUz7qICgFstqhGFlZHbmNLW6ntR88S0cFWfOd7JDOa9Yi9UCj50h6qm4hPDy-Yzlz14bqulucB-CpjD-VHY-XeRgJZJtxesyMqkqru8FC2BDyDUu-0KWkwWGDvZCseFcAE-3k7RiFKqKbXcljA925LiFzbjAjlX0byLoZwmlBJCTlfEoPmSBd-QntD5TxAFkG-8gFbq3Bw8',
                name: 'Heritage Restorations',
                time: 'Jan 12',
                message:
                    'We\'ve sourced the original chrome parts for your \'67 Mustang.',
                isOnline: false,
              ),

              const SizedBox(height: 32),

              // Support Floating Card
              _buildSupportCard(),
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
              currentIndex:
                  2, // <--- 2 porque es la tercera pantalla (Messages)
              onTap: (index) {
                if (index == 0)
                  Navigator.pushReplacementNamed(context, '/home');
                if (index == 1)
                  Navigator.pushReplacementNamed(context, '/workshops');
                // if (index == 3) Navigator.pushReplacementNamed(context, '/profile');
              }, // Messages is active
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

  Widget _buildActiveRequestCard() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.onPrimary,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Stack(
          children: [
            // Decorative background blur element
            Positioned(
              right: -40,
              top: -64,
              child: Container(
                width: 128,
                height: 128,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white.withOpacity(0.1),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: const Text(
                            'ACTIVE REQUEST',
                            style: TextStyle(
                              fontFamily: 'Inter',
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: AppColors.onPrimaryContainer,
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Downtown Precision Motors',
                          style: TextStyle(
                            fontFamily: 'Manrope',
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: AppColors.onPrimaryContainer,
                            height: 1.2,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Mechanic Elias is arriving in 4 mins',
                          style: TextStyle(
                            fontFamily: 'Inter',
                            fontSize: 14,
                            color: AppColors.onPrimaryContainer.withOpacity(
                              0.8,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      const Icon(
                        Icons.emergency_share,
                        color: AppColors.onPrimaryContainer,
                        size: 36,
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {},
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: AppColors.primary,
                          elevation: 4,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 8,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          minimumSize: Size.zero,
                        ),
                        child: const Text(
                          'VIEW MAP',
                          style: TextStyle(
                            fontFamily: 'Inter',
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
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
      ),
    );
  }

  Widget _buildChatItem({
    required String imageUrl,
    required String name,
    required String time,
    required String message,
    required bool isOnline,
  }) {
    return InkWell(
      onTap: () {},
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          children: [
            Stack(
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12),
                    image: DecorationImage(
                      image: NetworkImage(imageUrl),
                      fit: BoxFit.cover,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                ),
                if (isOnline)
                  Positioned(
                    right: -2,
                    bottom: -2,
                    child: Container(
                      width: 16,
                      height: 16,
                      decoration: BoxDecoration(
                        color: AppColors.primary,
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.surface, width: 2),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          name,
                          style: const TextStyle(
                            fontFamily: 'Manrope',
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.onSurface,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Text(
                        time,
                        style: const TextStyle(
                          fontFamily: 'Inter',
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: AppColors.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    message,
                    style: TextStyle(
                      fontFamily: 'Inter',
                      fontSize: 14,
                      fontWeight: isOnline ? FontWeight.w600 : FontWeight.w500,
                      color: isOnline
                          ? AppColors.onSurfaceVariant
                          : AppColors.onSurfaceVariant.withOpacity(0.7),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSupportCard() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.secondary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.contact_support,
              color: AppColors.secondary,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Need help with a claim?',
                  style: TextStyle(
                    fontFamily: 'Manrope',
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.onSurface,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Our 24/7 trust team is available to assist with insurance and dispute resolution.',
                  style: TextStyle(
                    fontFamily: 'Inter',
                    fontSize: 14,
                    color: AppColors.onSurfaceVariant,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () {},
                  style: TextButton.styleFrom(
                    padding: EdgeInsets.zero,
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                  child: const Text(
                    'CONTACT SUPPORT',
                    style: TextStyle(
                      fontFamily: 'Inter',
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: AppColors.secondary,
                      letterSpacing: 0.5,
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
