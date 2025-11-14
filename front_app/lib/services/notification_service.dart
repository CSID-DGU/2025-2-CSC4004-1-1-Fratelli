import 'package:dio/dio.dart';
import 'package:deepflect_app/services/api_service.dart';

class NotificationService {
  late final ApiService _apiService;
  
  NotificationService() {
    _apiService = ApiService();
  }

  // 알림 목록
  Future<List<Map<String, dynamic>>> getNotifications() async {
    try {
      print('알림 목록 요청');
      
      final response = await _apiService.getWithAuth('/api/v1/notification/myNotification');

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true && responseData['data'] != null) {
          final List<dynamic> dataList = responseData['data'];
          return dataList.map((item) => item as Map<String, dynamic>).toList();
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        throw Exception('알림 목록 조회 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');
      
      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 알림 삭제
  Future<void> deleteNotification(String id) async {
    try {
      print('알림 삭제 요청: $id');
      
      final response = await _apiService.deleteWithAuth(
        '/api/v1/notification/myNotification/$id',
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        print('알림 삭제 성공');
      } else {
        throw Exception('알림 삭제 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');
      
      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (e.response?.statusCode == 404) {
        throw Exception('알림을 찾을 수 없습니다.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }
}

