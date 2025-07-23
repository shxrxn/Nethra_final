class BehavioralData {
  final int sessionDuration;
  final int tapCount;
  final double averageTapPressure;
  final double averageTapDuration;
  final int swipeCount;
  final double averageSwipeVelocity;
  final double totalSwipeDistance;
  final double deviceTiltVariation;
  final List<double> movementPattern;
  final double typingRhythm;
  final double navigationFlow;
  final DateTime timestamp;
  
  BehavioralData({
    required this.sessionDuration,
    required this.tapCount,
    required this.averageTapPressure,
    required this.averageTapDuration,
    required this.swipeCount,
    required this.averageSwipeVelocity,
    required this.totalSwipeDistance,
    required this.deviceTiltVariation,
    required this.movementPattern,
    required this.typingRhythm,
    required this.navigationFlow,
    required this.timestamp,
  });
  
  Map<String, dynamic> toJson() {
    return {
      'session_duration': sessionDuration,
      'tap_count': tapCount,
      'average_tap_pressure': averageTapPressure,
      'average_tap_duration': averageTapDuration,
      'swipe_count': swipeCount,
      'average_swipe_velocity': averageSwipeVelocity,
      'total_swipe_distance': totalSwipeDistance,
      'device_tilt_variation': deviceTiltVariation,
      'movement_pattern': movementPattern,
      'typing_rhythm': typingRhythm,
      'navigation_flow': navigationFlow,
      'timestamp': timestamp.toIso8601String(),
    };
  }
  
  // Convert to backend API format
  Map<String, dynamic> toBackendFormat(int userId) {
    return {
      'user_id': userId,
      'avg_pressure': averageTapPressure,
      'avg_swipe_velocity': averageSwipeVelocity,
      'avg_swipe_duration': averageTapDuration / 1000, // Convert to seconds
      'accel_stability': deviceTiltVariation,
      'gyro_stability': deviceTiltVariation * 0.8, // Simulate gyro data
      'touch_frequency': sessionDuration > 0 ? tapCount / (sessionDuration / 60) : 0, // Per minute
      'timestamp': timestamp.toIso8601String(),
      'device_info': {
        'session_duration': sessionDuration,
        'total_swipes': swipeCount,
        'total_distance': totalSwipeDistance,
        'movement_pattern': movementPattern,
        'typing_rhythm': typingRhythm,
        'navigation_flow': navigationFlow,
      }
    };
  }
  
  factory BehavioralData.fromJson(Map<String, dynamic> json) {
    return BehavioralData(
      sessionDuration: json['session_duration'],
      tapCount: json['tap_count'],
      averageTapPressure: json['average_tap_pressure'],
      averageTapDuration: json['average_tap_duration'],
      swipeCount: json['swipe_count'],
      averageSwipeVelocity: json['average_swipe_velocity'],
      totalSwipeDistance: json['total_swipe_distance'],
      deviceTiltVariation: json['device_tilt_variation'],
      movementPattern: List<double>.from(json['movement_pattern']),
      typingRhythm: json['typing_rhythm'],
      navigationFlow: json['navigation_flow'],
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}