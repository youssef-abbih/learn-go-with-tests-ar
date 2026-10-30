# عودة إلى الوقت مع `testing/synctest`

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/synctest)**

في [فصل الوقت](time.md) منحنا تطبيق البوكر الذي يعمل من سطر الأوامر القدرة على جدولة تنبيهات "الرهان الأعمى يرتفع الآن"، باستعمال `time.AfterFunc`. وكان اختبار ذلك صعباً: فالدالة `time.AfterFunc` تشغّل دالة رد النداء (callback) الخاصة بها في `goroutine` مستقلة بعد انقضاء مدة حقيقية، ولا يمكنك مقارنة الدوال في غو، لذا لم نستطع بسهولة فحص ما جُدول.

وحللنا ذلك بأداة مألوفة: حقن التبعية (dependency injection). فقد عرّفنا الواجهة (interface) `BlindAlerter`، واستبدلنا في اختباراتنا بالتنفيذ الحقيقي جاسوساً (spy) لا يفعل إلا تسجيل ما طُلب منه جدولته، على نحو يشبه هذا:

```go
type BlindAlerter interface {
	ScheduleAlertAt(duration time.Duration, amount int)
}

type SpyBlindAlerter struct {
	Alerts []struct {
		At     time.Duration
		Amount int
	}
}

func (s *SpyBlindAlerter) ScheduleAlertAt(at time.Duration, amount int) {
	s.Alerts = append(s.Alerts, struct {
		At     time.Duration
		Amount int
	}{at, amount})
}
```

هذا تصميم جيد، والاختبارات التي يتيحها سريعة وموثوقة. لكن انظر جيداً إلى ما تغطيه فعلاً. فهي تتحقق من أشياء مثل "استُدعيت `ScheduleAlertAt` بالقيمتين `10 * time.Minute` و`200`". ولا تسمح أبداً لمنبّه *حقيقي* بالعمل. فالجزء الوحيد من الشيفرة الذي يستدعي `time.AfterFunc` فعلاً ويطبع شيئاً، أي الجزء الذي يحتمل فعلاً وجود أخطاء برمجية، لا يمرّ به أي اختبار أبداً.

وليس ذلك سهواً، بل هو موازنة. فاختبار منبّه حقيقي قائم على `time.AfterFunc` اختباراً سليماً سيعني إما انتظار دقائق حقيقية حتى ينتهي الاختبار، أو تقليص المدد إلى أجزاء من الثانية والأمل في ألا يكون الجهاز الذي يشغّل الاختبار مشغولاً إلى حد يمنعه من المواكبة. ولا يغري أي من الخيارين. لذا لم نكن نفعل ذلك ببساطة.

ومنذ غو 1.25 صار هناك خيار ثالث: [`testing/synctest`](https://pkg.go.dev/testing/synctest). فهي تتيح لنا تشغيل شيفرة حقيقية غير معدّلة تستعمل `time.Sleep` و`time.AfterFunc` وأخواتهما، داخل اختبار يتحكم في الوقت تحكماً كاملاً: بلا انتظار، وبلا تقلّب، وبلا تقليص للمدد مع الأمل في الأفضل.

في هذا الفصل سنبني ذلك المنبّه الحقيقي من الصفر، ونختبره بـ`synctest`. لكن لنستحق ذلك أولاً، بأن نرى بالضبط ما الذي تنقذنا منه.

## ما يكفي من المعلومات عن `testing/synctest`

تشغّل الحزمة `testing/synctest` دالة داخل **فقاعة** (bubble) معزولة. وداخل تلك الفقاعة:

* تستعمل الحزمة `time` ساعة مزيفة (fake clock). تبدأ عند منتصف الليل بالتوقيت العالمي المنسَّق (UTC) في الأول من يناير عام 2000، ولا تتحرك إلا إلى الأمام.
* لا يتقدم الوقت المزيف إلا حين تكون كل `goroutine` في الفقاعة **محجوبة حجباً دائماً** (durably blocked)، أي محجوبة بطريقة لا يستطيع فك حجبها إلا `goroutine` أخرى في الفقاعة نفسها. ويُعدّ من ذلك كل من `time.Sleep`، والاستقبال الحاجب من قناة أُنشئت داخل الفقاعة، و`sync.Cond.Wait`، و`sync.WaitGroup.Wait`. أما قفل `sync.Mutex` فلا يُعدّ منها، لأن الأقفال لا تُمسك عادةً إلا لمدة وجيزة.
* تشغّل `synctest.Test(t, f)` الدالة `f` في فقاعة جديدة، ولا تعود حتى تنتهي كل `goroutine` أُطلقت داخلها. وإن انتهى الأمر بالفقاعة إلى حجب دائم دون أي سبيل للتقدم، فإنها تُفشل الاختبار بوصفه جموداً (deadlock) بدلاً من أن تعلق إلى الأبد.
* تحجب `synctest.Wait()` الـ`goroutine` المستدعية حتى تصبح كل الـ`goroutines` *الأخرى* في الفقاعة محجوبة حجباً دائماً، ثم تعود. وهي الطريقة التي تدع بها العمل الجاري في الخلفية يستقر قبل إجراء أي توكيد.

هذا يكفي للبدء. وسنتعرف إلى بعض الحواف الأكثر حدة ونحن نمضي.

## اكتب الاختبار أولاً

لنبدأ بالأمر البديهي، قبل اللجوء إلى `synctest` أصلاً: منبّه من النوع `BlindAlerter` ينتظر، بعد أن يُعطى مدة ومقداراً، انقضاء تلك المدة ثم يكتب رسالة في مكان ما، ونختبره بالوقت الحقيقي.

```go
package poker

import (
	"bytes"
	"testing"
	"time"
)

func TestStdOutAlerter(t *testing.T) {
	out := &bytes.Buffer{}
	alerter := StdOutAlerter(out)

	alerter.ScheduleAlertAt(5*time.Second, 100)

	time.Sleep(6 * time.Second)

	want := "Blind is now 100"
	if out.String() != want {
		t.Errorf("got %q, want %q", out.String(), want)
	}
}
```

ننام مدة أطول قليلاً من موعد التنبيه المجدول (6 ثوانٍ لا 5) لنعطي الـ`goroutine` التي تطلقها `time.AfterFunc` لحظة كي تعمل فعلاً قبل أن نتحقق.

## حاول تشغيل الاختبار

لم نكتب أي شيفرة إنتاج بعد، لذا لن يُصرَّف هذا:

```
./blind_alerter_test.go:11:13: undefined: StdOutAlerter
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
package poker

import (
	"fmt"
	"io"
	"time"
)

// BlindAlerter schedules alerts for blind amounts.
type BlindAlerter interface {
	ScheduleAlertAt(duration time.Duration, amount int)
}

// BlindAlerterFunc allows you to implement BlindAlerter with a function.
type BlindAlerterFunc func(duration time.Duration, amount int)

// ScheduleAlertAt is BlindAlerterFunc's implementation of BlindAlerter.
func (a BlindAlerterFunc) ScheduleAlertAt(duration time.Duration, amount int) {
	a(duration, amount)
}

// StdOutAlerter returns a BlindAlerterFunc that schedules alerts and prints them to out.
func StdOutAlerter(out io.Writer) BlindAlerterFunc {
	return func(duration time.Duration, amount int) {
		time.AfterFunc(duration, func() {
			fmt.Fprintf(out, "Blind is now %d", amount)
		})
	}
}
```

شغّله:

```
=== RUN   TestStdOutAlerter
--- PASS: TestStdOutAlerter (6.00s)
PASS
ok  	github.com/quii/learn-go-with-tests/synctest/v1	6.191s
```

لقد نجح. لكنه يستغرق أيضاً ست ثوانٍ حقيقية، من أجل تنبيه واحد. ولعبتنا الفعلية تجدول أحد عشر تنبيهاً، يفصل بين بعضها ما يصل إلى ساعة وأربعين دقيقة. ولن ينتظر أحد ذلك في كل تشغيل للاختبارات، لذا عملياً إما أن يُتخطى هذا الاختبار، أو أن يُكتب بمدد صغيرة صغراً غير واقعي لا تشبه الشيء الحقيقي إلا شبهاً باهتاً. وهذه هي المشكلة التي وُجدت `synctest` لحلها.

## تقديم `synctest`

لنغلّف الاختبار نفسه بفقاعة، ونرَ ما يحدث إن كنا متفائلين أكثر من اللازم بما تفعله لنا "الساعة المزيفة":

```go
func TestStdOutAlerter(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		out := &bytes.Buffer{}
		alerter := StdOutAlerter(out)

		alerter.ScheduleAlertAt(5*time.Second, 100)

		want := "Blind is now 100"
		if out.String() != want {
			t.Errorf("got %q, want %q", out.String(), want)
		}
	})
}
```

حذفنا النوم كلياً: فالساعة المزيفة ستتولى ذلك عنا الآن بالتأكيد، أليس كذلك؟ لا:

```
=== RUN   TestStdOutAlerter
    blind_alerter_test.go:19: got "", want "Blind is now 100"
--- FAIL: TestStdOutAlerter (0.00s)
FAIL
```

الساعة المزيفة للفقاعة لا تدفع نفسها إلى الأمام بمؤقّت (timer) خاص بها. فهي لا تتقدم إلا حين يُحجب شيء ما في الفقاعة حجباً دائماً، منتظراً تقدّمها. فما زال علينا أن نقول ما الذي ننتظره، لكننا لم نعد ندفع ثمنه بثوانٍ حقيقية. لنُعِد النوم إذن:

```go
func TestStdOutAlerter(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		out := &bytes.Buffer{}
		alerter := StdOutAlerter(out)

		alerter.ScheduleAlertAt(5*time.Second, 100)

		time.Sleep(6 * time.Second)

		want := "Blind is now 100"
		if out.String() != want {
			t.Errorf("got %q, want %q", out.String(), want)
		}
	})
}
```

```
=== RUN   TestStdOutAlerter
--- PASS: TestStdOutAlerter (0.00s)
PASS
ok  	github.com/quii/learn-go-with-tests/synctest/v2	0.133s
```

نجح، وفوراً: فاستدعاء `time.Sleep(6 * time.Second)` داخل فقاعة لا يكلف شيئاً من الوقت الحقيقي. يبدو أننا انتهينا. لنتحقق فقط، بحكم العادة، من أنه يصمد مع `-race`:

```
go test -race ./...
```

```
==================
WARNING: DATA RACE
Read at 0x00c00010e630 by goroutine 9:
  bytes.(*Buffer).String()
      /usr/local/go/src/bytes/buffer.go:77 +0x174
  github.com/quii/learn-go-with-tests/synctest/v2.TestStdOutAlerter.func1()
      blind_alerter_test.go:20 +0x15c
  testing.tRunner()
      /usr/local/go/src/testing/testing.go:1934 +0x164

Previous write at 0x00c00010e630 by goroutine 11:
  bytes.(*Buffer).grow()
      /usr/local/go/src/bytes/buffer.go:143 +0x354
  bytes.(*Buffer).Write()
      /usr/local/go/src/bytes/buffer.go:185 +0xb4
  fmt.Fprintf()
      /usr/local/go/src/fmt/print.go:225 +0x94
  github.com/quii/learn-go-with-tests/synctest/v2.TestStdOutAlerter.func1.BlindAlerterFunc.ScheduleAlertAt.TestStdOutAlerter.func1.StdOutAlerter.1.2()
      blind_alerter.go:26 +0x6c

Goroutine 11 (finished) created at:
  time.goFunc()
      /usr/local/go/src/time/sleep.go:215 +0x40
==================
--- FAIL: TestStdOutAlerter (0.00s)
    testing.go:1617: race detected during execution of test
FAIL
```

يا للألم. لاحظ عبارة "Goroutine 11 (finished)": فالكتابة حدثت فعلاً قبل قراءتنا، في كل مرة شغّلناه فيها. فمن الناحية الوظيفية، لا يمكن للاختبار أبداً أن يفشل في التوكيد. لكن كاشف التسابق (race detector) لا يسأل "هل حدث خطأ هذه المرة؟"، بل يسأل "هل هناك ما *يضمن* أنه لا يمكن أن يحدث؟". فاستدعاء `time.Sleep` في الـ`goroutine` الخاصة بنا ودالة رد النداء الخاصة بـ`time.AfterFunc` في `goroutine` مستقلة ليسا إلا اثنتين من الـ`goroutines` تُجدول كل منهما على حدة. ولا شيء في عبارة "نمت مدة من الوقت" يعد بأن `goroutine` أخرى قد انتهت من لمس الذاكرة المشتركة، مهما كان النوم سخياً. والنوم مدة أطول لا يصلح هذا، مهما طالت، بل يجعله يفشل أقل فحسب خارج `-race`.

ويستحق الأمر أن نتأمله لحظة: فهذا التسابق نفسه كان كامناً من قبل في نسختنا الأولى البسيطة القائمة على الوقت الحقيقي أيضاً، مع `time.Sleep` حقيقية. لكننا لم نفكر قط في التحقق من ذلك: فمن ذا الذي يشغّل `-race` مراراً على اختبار يستغرق تشغيله أصلاً ست ثوانٍ حقيقية؟

## اكتب الاختبار أولاً

ما نحتاج إليه نقطة تزامن (synchronization point) حقيقية: شيء لا يجعل الكتابة تحدث أولاً *على الأرجح* فقط، بل يثبت فعلاً أنها حدثت. وهذا بالضبط ما وُجدت `synctest.Wait()` من أجله:

```go
func TestStdOutAlerter(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		out := &bytes.Buffer{}
		alerter := StdOutAlerter(out)

		alerter.ScheduleAlertAt(5*time.Second, 100)

		time.Sleep(6 * time.Second)
		synctest.Wait()

		want := "Blind is now 100"
		if out.String() != want {
			t.Errorf("got %q, want %q", out.String(), want)
		}
	})
}
```

## أعد الهيكلة

لا شيء يحتاج إلى تغيير في شيفرة الإنتاج، لكن لنتأكد من أن هذا الاختبار يصمد فعلاً، مراراً، مع `-race`:

```
ok  	github.com/quii/learn-go-with-tests/synctest/v3	1.153s
ok  	github.com/quii/learn-go-with-tests/synctest/v3	1.143s
ok  	github.com/quii/learn-go-with-tests/synctest/v3	1.148s
ok  	github.com/quii/learn-go-with-tests/synctest/v3	1.147s
ok  	github.com/quii/learn-go-with-tests/synctest/v3	1.143s
```

نظيف في كل مرة. رائع جداً.

## اكتب الاختبار أولاً

هناك أمر آخر يستحق الاختبار: أن شيئاً لم يحدث بعد. فمع الوقت الحقيقي، يعني هذا تخمين مدة نوم طويلة بما يكفي لنكون واثقين، لكن ليست طويلة إلى حد يجعل الاختبار متثاقلاً. أما الحزمة `synctest` فلا تحتاج إلى التخمين:

```go
func TestStdOutAlerter(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		out := &bytes.Buffer{}
		alerter := StdOutAlerter(out)

		alerter.ScheduleAlertAt(5*time.Second, 100)

		synctest.Wait()
		if out.String() != "" {
			t.Errorf("did not expect anything to be printed yet, got %q", out.String())
		}

		time.Sleep(5 * time.Second)
		synctest.Wait()

		want := "Blind is now 100"
		if out.String() != want {
			t.Errorf("got %q, want %q", out.String(), want)
		}
	})
}
```

لا شيء آخر في الفقاعة يفعل أي شيء لحظة جدولة التنبيه، لذا ينبغي أن تعود `Wait()` فوراً: فلا شيء يُنتظر *من أجله* بعد، وينبغي أن يظل `out` فارغاً. شغّله:

```
=== RUN   TestStdOutAlerter
--- PASS: TestStdOutAlerter (0.00s)
PASS
```

نجح. لنتحقق من `-race`، كما نعرف الآن أن علينا أن نفعل:

```
==================
WARNING: DATA RACE
Write at 0x00c00011c630 by goroutine 11:
  bytes.(*Buffer).grow()
      /usr/local/go/src/bytes/buffer.go:143 +0x354
  bytes.(*Buffer).Write()
      /usr/local/go/src/bytes/buffer.go:185 +0xb4
  fmt.Fprintf()
      /usr/local/go/src/fmt/print.go:225 +0x94
  github.com/quii/learn-go-with-tests/synctest/v4.TestStdOutAlerter.func1.BlindAlerterFunc.ScheduleAlertAt.TestStdOutAlerter.func1.StdOutAlerter.1.2()
      blind_alerter.go:26 +0x6c

Previous read at 0x00c00011c630 by goroutine 9:
  bytes.(*Buffer).String()
      /usr/local/go/src/bytes/buffer.go:77 +0x164
  github.com/quii/learn-go-with-tests/synctest/v4.TestStdOutAlerter.func1()
      blind_alerter_test.go:18 +0x14c
  testing.tRunner()
      /usr/local/go/src/testing/testing.go:1934 +0x164

Goroutine 11 (running) created at:
  time.goFunc()
      /usr/local/go/src/time/sleep.go:215 +0x40
==================
--- FAIL: TestStdOutAlerter (0.00s)
    testing.go:1617: race detected during execution of test
FAIL
```

التسابق في السطر 18: أي في تحققنا الأول تماماً، ذاك الذي كنا واثقين منه، لأنه "لا شيء يُنتظر بعد". وبشكل موثوق، في كل تشغيل.

المشكلة أن `Wait()` وحدها لا تملك ما يحدّ المدى الذي تسمح للساعة المزيفة بأن تجري إليه. فلا `goroutine` أخرى في الفقاعة في تلك اللحظة، ولا موعد قادم *ننتظره نحن*. ولم يتبقَّ إلا مؤقّت التنبيه ذو الثواني الخمس، القابع في كومة المؤقّتات (timer heap) الخاصة بوقت التشغيل. فيفعل وقت التشغيل الشيء المفيد الوحيد الذي يستطيعه: يطلق المؤقّت كي يتقدم، فيُطلق الـ`goroutine` رقم 11 لتشغيل دالة رد النداء الخاصة بنا، *بينما* لا تزال `Wait()` تقرر هل تعود أم لا. فالـ`goroutine` رقم 11 تعمل فعلاً بالتزامن مع تحققنا، لا قبله. وأحياناً تنتهي تلك الكتابة أولاً، وأحياناً لا. وقيمة `bytes.Buffer` التي نلمسها كلانا لا قفل لها، فلا شيء يجعل ذلك آمناً في أي من الحالتين.

يمكننا إصلاح هذا كما نصلح أي تسابق بيانات (data race): بتغليف `out` بـ`sync.Mutex`، أو باستعمال `atomic.Pointer[T]` من الحزمة `sync/atomic` كحل أخف. لكن انظر إلى ما يُطلب فعلاً من `StdOutAlerter`: أن يقرر الرسالة *وأن* ينفذ الأثر الجانبي (side effect) المتمثل في طباعتها. ولا شيء في جدولة تنبيه رهان أعمى في البوكر يتطلب معرفة `io.Writer`، فهذا شأن المستدعي. وهذا هو شكل التوتر الذي يعود إليه هذا الكتاب مرة بعد مرة: [إن كانت اختباراتك تسبب لك الألم، فأصغِ إلى تلك الإشارة وفكّر في تصميم شيفرتك](http-handlers-revisited.md). فلنجعل المنبّه لا يفعل إلا إنتاج الرسالة حين يحين موعدها، ولندع المستدعي يقرر ما يفعل بها.

## أعد الهيكلة

عبور الحدود بين الـ`goroutines` هو بالضبط ما وُجدت القنوات من أجله. وكما يقول أحد أمثال غو، [لا تتواصل بمشاركة الذاكرة؛ بل شارك الذاكرة بالتواصل](https://go.dev/blog/codelab-share). فبدلاً من الكتابة في `out` مشتركة، يستطيع منبّهنا إرسال الرسالة الجاهزة عبر قناة:

```go
func NewAlerter() (BlindAlerterFunc, <-chan string) {
	alerts := make(chan string)

	scheduleAlertAt := func(duration time.Duration, amount int) {
		time.AfterFunc(duration, func() {
			alerts <- fmt.Sprintf("Blind is now %d", amount)
		})
	}

	return scheduleAlertAt, alerts
}
```

يبقى كل من `BlindAlerter` و`BlindAlerterFunc` كما كانا تماماً. ولم يختفِ إلا `StdOutAlerter` (الذي، وهذا معبّر، لم تعد له أي علاقة بالمخرجات القياسية `stdout`)، وحلّت محله `NewAlerter`، التي تعيد المنبّه وقناة نستقبل منها معاً. وأياً كان الطرف الذي يريد طباعة هذه التنبيهات (`main` مثلاً)، فبإمكانه المرور بـ`range` على تلك القناة وطباعتها، ولم يعد ذلك مشكلة هذه الحزمة.

ويصبح الاختبار أبسط أيضاً:

```go
func TestNewAlerter(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		alerter, alerts := NewAlerter()

		alerter.ScheduleAlertAt(5*time.Second, 100)

		select {
		case got := <-alerts:
			t.Fatalf("did not expect an alert yet, got %q", got)
		default:
		}

		got := <-alerts
		want := "Blind is now 100"
		if got != want {
			t.Errorf("got %q, want %q", got, want)
		}
	})
}
```

لاحظ ما اختفى: لا `synctest.Wait()` في أي مكان، ولا نوع مخصص لحماية قيمة مشتركة، ولا `time.Sleep` على الإطلاق. فلم نعد نحتاج إلى أي منها.

التعليمة `select` مع حالة `default`، المأخوذة مباشرة من [فصل `select`](select.md)، لا تحجب أبداً: فهي إما تأخذ حالة جاهزة أو تنتقل فوراً إلى `default`. وفي هذه اللحظة لا يزال الوقت الافتراضي واقفاً عند الصفر، أي قبل التنبيه بخمس ثوانٍ (مزيفة) كاملة، فلا شيء يحتاج إلى تزامن: وبالطبع لم يصل شيء بعد. أما `got := <-alerts` فلا تحتاج إلى دفعة أيضاً: فهي استقبال حاجب عادي، لذا تفعل الفقاعة بالضبط ما صُممت لفعله: بما أن الشيء الوحيد الذي ينتظره أي طرف في الفقاعة هو ذلك المؤقّت، يقفز الوقت المزيف مباشرة إلى لحظة إطلاقه، فيوقظ الـ`goroutine` الخاصة بـ`time.AfterFunc`، ويفك حجب استقبالنا.

شغّل هذا مع `-race` مراراً. سيظل أخضر: فلم تبقَ ذاكرة مشتركة يمكن التسابق عليها.

قارن هذا بأسلوب `SpyBlindAlerter` من الفصل السابق. فذاك لا يزال أداة جيدة تماماً لمهمة مختلفة: إذ يتحقق مما *يُجدول* (هل تُجدول المقادير الصحيحة عند الفواصل الزمنية الصحيحة لعدد معين من اللاعبين؟) دون أن يكترث بالتوقيت الحقيقي على الإطلاق (وهذا مفيد حين تختبر الحساب لا التوقيت). ولم تحل `synctest` محل تلك الحاجة، بل تسد فجوة التغطية التي يتركها دائماً جاسوس لا يعرف إلا "ما الذي طُلب مني فعله": هل تعمل آلية الجدولة نفسها فعلاً؟

## الخلاصة

### ما تناولناه

* الدالة `synctest.Test` وفكرة الفقاعة ذات الساعة المزيفة المعزولة، التي لا تتقدم إلا حين يُحجب شيء ما حجباً دائماً، لا من تلقاء نفسها.
* مفهوم "المحجوب حجباً دائماً": الشرط الذي يتيح للوقت المزيف أن يتقدم، ولماذا لا يُعدّ `sync.Mutex` منه عمداً (بينما يُعدّ الاستقبال من قناة منه).
* النوم "مدة كافية" ليس كالتزامن: فحتى النوم السخي الصحيح دائماً من الناحية العملية يظل تسابق بيانات حقيقياً إن لم يكن هناك ما يفرض الترتيب.
* تصلح `synctest.Wait()` ذلك لتحقق واحد، لكن استدعاءها دون أي شيء آخر في الفقاعة يحدّها قد يدع الساعة المزيفة تجري أبعد مما قصدت، وهذا بالضبط ما حدث عند اختبار حالة "لم يحدث شيء بعد".
* اختبار يكشف مشكلة في التصميم، لا مجرد خطأ برمجي، وإصلاح التصميم بدلاً من اللجوء إلى قفل.

### مزالق ينبغي الانتباه إليها

* إن ظلت `goroutine` في الفقاعة محجوبة حجباً دائماً حين تعود الدالة الجذرية للفقاعة، فإن `synctest.Test` تُفشل الاختبار بوصفه جموداً بدلاً من أن تعلق، فتأكد من أن الـ`goroutines` العاملة في الخلفية تنتهي فعلاً.
* القنوات والمؤقّتات والمؤقّتات الدورية (tickers) مرتبطة بالفقاعة التي أُنشئت فيها، واستعمال أي منها من خارج فقاعته يطلق الذعر.
* عمليات الإدخال والإخراج الحقيقية على الشبكة والملفات ليست حاجبة حجباً دائماً، لذا لا يمكنك التحكم بها مباشرة عبر الساعة المزيفة الخاصة بـ`synctest`، فاستعن بشيء مثل `net.Pipe` إن احتجت إلى بديل في الذاكرة.
* تعمل دالة رد النداء الخاصة بـ`time.AfterFunc` في `goroutine` خاصة بها، دون أي من ضمانات التزامن التي تمنحك إياها القناة. فإن اضطرت إلى لمس حالة مشتركة مباشرة، فتلك الحالة تحتاج إلى قفل خاص بها، كأي شيفرة متزامنة أخرى.

### مواد إضافية

* [مدونة غو: اختبار الشيفرة المتزامنة باستعمال testing/synctest](https://go.dev/blog/synctest)
* [توثيق الحزمة `testing/synctest`](https://pkg.go.dev/testing/synctest)
* [ملاحظات إصدار غو 1.25](https://go.dev/doc/go1.25)

### ملاحظة حول كيفية كتابة هذا الفصل

هذا أول فصل في الكتاب يُكتب بمساعدة الذكاء الاصطناعي (Claude). وأريد أن أكون صريحاً في ذلك، وفيما عنته "المساعدة" هنا فعلاً، لأنها لم تكن "صِف فصلاً، تحصل على فصل".

بدت العملية كثيراً مثل حلقة `TDD` التي يعلّمها هذا الكتاب من أوله إلى آخره: البحث في توثيق `testing/synctest` الحقيقي وشيفرته المصدرية بدلاً من التخمين، وكتابة برامج تجريبية صغيرة للاستكشاف ثم رميها للتحقق من الادعاءات قبل كتابة كلمة واحدة من النص، ومعاملة كل ادعاء في التوثيق على أنه شيء يجب التحقق منه بتشغيل حقيقي لـ`go test -race`، لا شيء يُصدَّق مباشرة. وكثير من المزالق في هذا الفصل، وأبرزها التفاعل بين `Wait()` وكاشف التسابق، لم توجد هنا إلا لأن اختباراً فشل فعلاً بطريقة غير متوقعة، على مدى عدة جولات من التشغيل الفعلي، وكان لا بد من التنقيب في السبب قبل تقرير ما يُكتب.

وقد تغيّر شكل التصميم نفسه في منتصف الطريق أيضاً. فقد كان `StdOutAlerter` في المسودة الأولى يكتب مباشرة في `io.Writer`، وهذا بالضبط نوع الأشياء التي طالما اعترض عليها هذا الكتاب حين يبدأ اختبار ما بالإيلام: [إن كانت اختباراتك تسبب لك الألم، فأصغِ إلى تلك الإشارة وفكّر في تصميم شيفرتك](http-handlers-revisited.md). ففعلنا ذلك، وانتهى بنا الأمر إلى النسخة القائمة على القنوات أعلاه، وإلى فصل أقصر وأفضل بفضلها.

كل ما هنا رُوجع وحُرّر، وجرى الاعتراض عليه أكثر من مرة: حين لم تكن النبرة تبدو صحيحة، وحين تضخم قسم ما متجاوزاً ما يستحقه الدرس الفعلي، وحين لجأ شرح ما إلى المصطلحات المتخصصة في حين كان عرض فشل حقيقي لاختبار سيؤدي المهمة على نحو أفضل. وإن بدا شيء هنا غريباً في قراءته، فاللوم عليّ أنا، لا على الأداة.
