import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_app/main.dart';

void main() {
  testWidgets('Smoke test de inicialização do app AutoFlow', (WidgetTester tester) async {
    await tester.pumpWidget(const AutoFlowApp());
    expect(find.byType(AutoFlowApp), findsOneWidget);
  });
}
