# تنفيذ أوامر نظام التشغيل

**[تجد كل الشيفرة هنا](https://github.com/quii/learn-go-with-tests/tree/main/q-and-a/os-exec)**

يسأل [keith6014](https://www.reddit.com/user/keith6014) على [reddit](https://www.reddit.com/r/golang/comments/aaz8ji/testdata_and_function_setup_help/)

> أنفّذ أمراً باستعمال `os/exec.Command()` يولّد بيانات XML. وسيُنفَّذ الأمر في دالة اسمها `GetData()`.

> ولكي أختبر `GetData()`، لدي بعض بيانات الاختبار التي أنشأتها.

> في ملف `_test.go` لدي `TestGetData` تستدعي `GetData()`، لكنها ستستعمل `os.exec`، وأريد بدلاً من ذلك أن تستعمل بيانات الاختبار الخاصة بي.

> ما الطريقة الجيدة لتحقيق ذلك؟ هل ينبغي عند استدعاء `GetData` أن يكون لدي وضع "اختبار" بالراية كي تقرأ ملفاً، أي `GetData(mode string)`؟

بعض الملاحظات

- حين يكون شيء ما صعب الاختبار، فكثيراً ما يكون السبب أن فصل الاهتمامات ليس صحيحاً تماماً
- لا تُضف "أوضاع اختبار" إلى شيفرتك (code)، بل استعمل [حقن التبعية](./dependency-injection.md) كي تستطيع نمذجة تبعياتك وفصل الاهتمامات.

سمحت لنفسي بتخمين ما قد تبدو عليه الشيفرة

```go
type Payload struct {
	Message string `xml:"message"`
}

func GetData() string {
	cmd := exec.Command("cat", "msg.xml")

	out, _ := cmd.StdoutPipe()
	var payload Payload
	decoder := xml.NewDecoder(out)

	// these 3 can return errors but I'm ignoring for brevity
	cmd.Start()
	decoder.Decode(&payload)
	cmd.Wait()

	return strings.ToUpper(payload.Message)
}
```

- تستعمل `exec.Command` التي تتيح لك تنفيذ أمر خارجي للعملية
- نلتقط المخرجات في `cmd.StdoutPipe` التي تعيد لنا `io.ReadCloser` (وسيصبح هذا مهماً)
- بقية الشيفرة منسوخة ومُلصقة تقريباً من [التوثيق الممتاز](https://golang.org/pkg/os/exec/#example_Cmd_StdoutPipe).
    - نلتقط أي مخرجات من `stdout` في `io.ReadCloser`، ثم نبدأ الأمر بـ`Start`، ثم ننتظر قراءة كل البيانات باستدعاء `Wait`. وبين هذين الاستدعاءين نفك ترميز البيانات إلى البنية (struct) `Payload`.

إليك ما يحتويه `msg.xml`

```xml
<payload>
    <message>Happy New Year!</message>
</payload>
```

كتبت اختباراً (test) بسيطاً لأبيّنه عملياً

```go
func TestGetData(t *testing.T) {
	got := GetData()
	want := "HAPPY NEW YEAR!"

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}
```

## الشيفرة القابلة للاختبار

الشيفرة القابلة للاختبار منفصلة الأجزاء وأحادية الغرض. ويبدو لي أن لهذه الشيفرة اهتمامين أساسيين

1. استرجاع بيانات XML الخام
2. فك ترميز بيانات XML وتطبيق منطق الأعمال (في هذه الحالة `strings.ToUpper` على `<message>`)

الجزء الأول ليس إلا نسخاً للمثال من المكتبة القياسية.

أما الجزء الثاني ففيه منطق الأعمال لدينا، وبالنظر إلى الشيفرة نرى أين يبدأ "الدرز" في منطقنا؛ إنه حيث نحصل على `io.ReadCloser`. ويمكننا استعمال هذا التجريد الموجود لفصل الاهتمامات وجعل شيفرتنا قابلة للاختبار.

**المشكلة في `GetData` أن منطق الأعمال مقترن بوسيلة الحصول على XML. ولتحسين تصميمنا علينا فك الاقتران بينهما**

يمكن أن يكون `TestGetData` اختبار التكامل بين اهتمامينا، لذا سنحتفظ به للتأكد من أنه يظل يعمل.

إليك كيف تبدو الشيفرة بعد فصلها

```go
type Payload struct {
	Message string `xml:"message"`
}

func GetData(data io.Reader) string {
	var payload Payload
	xml.NewDecoder(data).Decode(&payload)
	return strings.ToUpper(payload.Message)
}

func getXMLFromCommand() io.Reader {
	cmd := exec.Command("cat", "msg.xml")
	out, _ := cmd.StdoutPipe()

	cmd.Start()
	data, _ := io.ReadAll(out)
	cmd.Wait()

	return bytes.NewReader(data)
}

func TestGetDataIntegration(t *testing.T) {
	got := GetData(getXMLFromCommand())
	want := "HAPPY NEW YEAR!"

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}
```

والآن بعد أن صارت `GetData` تأخذ مدخلاتها من `io.Reader` فقط، جعلناها قابلة للاختبار، ولم تعد تهتم بطريقة استرجاع البيانات؛ فيستطيع الناس إعادة استعمال الدالة (function) مع أي شيء يعيد `io.Reader` (وهذا شائع جداً). فمثلاً يمكننا البدء بجلب XML من عنوان URL بدلاً من سطر الأوامر.

```go
func TestGetData(t *testing.T) {
	input := strings.NewReader(`
<payload>
    <message>Cats are the best animal</message>
</payload>`)

	got := GetData(input)
	want := "CATS ARE THE BEST ANIMAL"

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
}

```

إليك مثالاً على اختبار وحدة للدالة `GetData`.

وبفصل الاهتمامات واستعمال التجريدات الموجودة في غو (Go)، يصبح اختبار منطق أعمالنا المهم أمراً يسيراً.
