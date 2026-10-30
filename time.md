# الوقت

[**تجد كل شيفرة هذا الفصل هنا**](https://github.com/quii/learn-go-with-tests/tree/main/time)

تريد مالكة المنتج أن نوسّع وظائف تطبيق سطر الأوامر بمساعدة مجموعة من الناس على لعب بوكر تكساس هولدم.

## ما يكفي من المعلومات عن البوكر

لن تحتاج إلى معرفة الكثير عن البوكر، إلا أن على جميع اللاعبين أن يُبلَّغوا على فترات زمنية معيّنة بقيمة "الرهان الأعمى" التي تتزايد باطراد.

سيساعد تطبيقنا على تتبع متى ينبغي أن يرتفع الرهان الأعمى، وبكم.

- حين يبدأ، يسأل عن عدد اللاعبين. وهذا يحدد مقدار الوقت قبل أن يرتفع الرهان "الأعمى".
  - هناك مقدار أساسي من الوقت قدره 5 دقائق.
  - وتُضاف دقيقة واحدة لكل لاعب.
  - فمثلاً 6 لاعبين يساوون 11 دقيقة للرهان الأعمى.
- بعد انقضاء وقت الرهان الأعمى، ينبغي أن تنبّه اللعبة اللاعبين إلى المقدار الجديد للرهان الأعمى.
- يبدأ الرهان الأعمى بـ100 فيشة، ثم 200، و400، و600، و1000، و2000، ويستمر في التضاعف حتى تنتهي اللعبة (ينبغي أن تظل وظيفتنا السابقة "Ruth wins" تنهي اللعبة)

## تذكير بالشيفرة

بدأنا في الفصل السابق تطبيق سطر الأوامر الذي يقبل بالفعل الأمر `{name} wins`. إليك كيف تبدو شيفرة `CLI` الحالية، لكن تأكد من الاطلاع على الشيفرة (code) الأخرى أيضاً قبل البدء.

```go
type CLI struct {
	playerStore PlayerStore
	in          *bufio.Scanner
}

func NewCLI(store PlayerStore, in io.Reader) *CLI {
	return &CLI{
		playerStore: store,
		in:          bufio.NewScanner(in),
	}
}

func (cli *CLI) PlayPoker() {
	userInput := cli.readLine()
	cli.playerStore.RecordWin(extractWinner(userInput))
}

func extractWinner(userInput string) string {
	return strings.Replace(userInput, " wins", "", 1)
}

func (cli *CLI) readLine() string {
	cli.in.Scan()
	return cli.in.Text()
}
```


### الدالة `time.AfterFunc`

نريد أن نستطيع جدولة برنامجنا لطباعة قيم الرهان الأعمى بعد مدد معيّنة تعتمد على عدد اللاعبين.

لتقليص نطاق ما علينا فعله، سننسى جزء عدد اللاعبين في الوقت الحالي، ونفترض فقط أن هناك 5 لاعبين، لذا سنختبر أن _القيمة الجديدة للرهان الأعمى تُطبع كل 10 دقائق_.

كالعادة، المكتبة القياسية تكفينا ذلك بـ[`func AfterFunc(d Duration, f func()) *Timer`](https://golang.org/pkg/time/#AfterFunc)

> تنتظر `AfterFunc` انقضاء المدة، ثم تستدعي `f` في `goroutine` خاصة بها. وتعيد `Timer` يمكن استعماله لإلغاء الاستدعاء باستعمال طريقته `Stop`.

### النوع [`time.Duration`](https://golang.org/pkg/time/#Duration)

> يمثل `Duration` الوقت المنقضي بين لحظتين كعدد من النانوثواني من النوع `int64`.

في مكتبة الوقت عدد من الثوابت تتيح لك ضرب تلك النانوثواني لتصبح أسهل قراءة قليلاً في نوع السيناريوهات التي سنتعامل معها

```
5 * time.Second
```

حين نستدعي `PlayPoker` سنجدول كل تنبيهات الرهان الأعمى.

لكن اختبار هذا قد يكون صعباً بعض الشيء. فسنريد التحقق من أن كل فترة زمنية مجدولة بمقدار الرهان الأعمى الصحيح، لكن إن نظرت إلى توقيع `time.AfterFunc` فستجد أن وسيطه (argument) الثاني هو الدالة التي سيشغّلها. ولا يمكنك مقارنة الدوال في غو (Go)، لذا لن نستطيع اختبار الدالة التي أُرسلت. لذا سنحتاج إلى كتابة نوع من الأغلفة حول `time.AfterFunc` يأخذ وقت التشغيل والمقدار المراد طباعته، كي نستطيع التجسس على ذلك.

## اكتب الاختبار أولاً

أضف اختباراً (test) جديداً إلى مجموعتنا

```go
t.Run("it schedules printing of blind values", func(t *testing.T) {
	in := strings.NewReader("Chris wins\n")
	playerStore := &poker.StubPlayerStore{}
	blindAlerter := &SpyBlindAlerter{}

	cli := poker.NewCLI(playerStore, in, blindAlerter)
	cli.PlayPoker()

	if len(blindAlerter.alerts) != 1 {
		t.Fatal("expected a blind alert to be scheduled")
	}
})
```

ستلاحظ أننا صنعنا `SpyBlindAlerter` نحاول حقنه في `CLI`، ثم نتحقق من أن تنبيهاً قد جُدول بعد استدعاء `PlayPoker`.

(تذكّر أننا نبدأ بأبسط سيناريو أولاً ثم نتقدم خطوة خطوة.)

إليك تعريف `SpyBlindAlerter`

```go
type SpyBlindAlerter struct {
	alerts []struct {
		scheduledAt time.Duration
		amount      int
	}
}

func (s *SpyBlindAlerter) ScheduleAlertAt(duration time.Duration, amount int) {
	s.alerts = append(s.alerts, struct {
		scheduledAt time.Duration
		amount      int
	}{duration, amount})
}
```


## حاول تشغيل الاختبار

```
./CLI_test.go:32:27: too many arguments in call to poker.NewCLI
	have (*poker.StubPlayerStore, *strings.Reader, *SpyBlindAlerter)
	want (poker.PlayerStore, io.Reader)
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أضفنا وسيطاً جديداً والمصرِّف (compiler) يعترض. _بالمعنى الدقيق_ فإن أقل قدر من الشيفرة هو جعل `NewCLI` تقبل `*SpyBlindAlerter`، لكن لنغش قليلاً ونعرّف التبعية كواجهة (interface) فحسب.

```go
type BlindAlerter interface {
	ScheduleAlertAt(duration time.Duration, amount int)
}
```

ثم أضفها إلى الدالة البانية

```go
func NewCLI(store PlayerStore, in io.Reader, alerter BlindAlerter) *CLI
```

ستفشل اختباراتك الأخرى الآن لأنها لا تمرر `BlindAlerter` إلى `NewCLI`.

التجسس على `BlindAlerter` لا علاقة له بالاختبارات الأخرى، لذا أضف في ملف الاختبار

```go
var dummySpyAlerter = &SpyBlindAlerter{}
```

ثم استعمل ذلك في الاختبارات الأخرى لإصلاح مشكلات التصريف. وبتسميته "دمية" يتضح لقارئ الاختبار أنه غير مهم.

[> الكائنات الدمى تُمرَّر هنا وهناك لكنها لا تُستعمل فعلاً. وعادةً لا تُستعمل إلا لملء قوائم المعاملات.](https://martinfowler.com/articles/mocksArentStubs.html)

ينبغي أن تُصرَّف الاختبارات الآن، وأن يفشل اختبارنا الجديد.

```
=== RUN   TestCLI
=== RUN   TestCLI/it_schedules_printing_of_blind_values
--- FAIL: TestCLI (0.00s)
    --- FAIL: TestCLI/it_schedules_printing_of_blind_values (0.00s)
    	CLI_test.go:38: expected a blind alert to be scheduled
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

سنحتاج إلى إضافة `BlindAlerter` كحقل في `CLI` كي نستطيع الإشارة إليه في الطريقة (method) `PlayPoker`.

```go
type CLI struct {
	playerStore PlayerStore
	in          *bufio.Scanner
	alerter     BlindAlerter
}

func NewCLI(store PlayerStore, in io.Reader, alerter BlindAlerter) *CLI {
	return &CLI{
		playerStore: store,
		in:          bufio.NewScanner(in),
		alerter:     alerter,
	}
}
```

لجعل الاختبار ينجح، يمكننا استدعاء `BlindAlerter` بأي شيء نريده

```go
func (cli *CLI) PlayPoker() {
	cli.alerter.ScheduleAlertAt(5*time.Second, 100)
	userInput := cli.readLine()
	cli.playerStore.RecordWin(extractWinner(userInput))
}
```

بعد ذلك سنريد التحقق من أنه يجدول كل التنبيهات التي نرجوها لـ5 لاعبين

## اكتب الاختبار أولاً

```go
	t.Run("it schedules printing of blind values", func(t *testing.T) {
		in := strings.NewReader("Chris wins\n")
		playerStore := &poker.StubPlayerStore{}
		blindAlerter := &SpyBlindAlerter{}

		cli := poker.NewCLI(playerStore, in, blindAlerter)
		cli.PlayPoker()

		cases := []struct {
			expectedScheduleTime time.Duration
			expectedAmount       int
		}{
			{0 * time.Second, 100},
			{10 * time.Minute, 200},
			{20 * time.Minute, 300},
			{30 * time.Minute, 400},
			{40 * time.Minute, 500},
			{50 * time.Minute, 600},
			{60 * time.Minute, 800},
			{70 * time.Minute, 1000},
			{80 * time.Minute, 2000},
			{90 * time.Minute, 4000},
			{100 * time.Minute, 8000},
		}

		for i, c := range cases {
			t.Run(fmt.Sprintf("%d scheduled for %v", c.expectedAmount, c.expectedScheduleTime), func(t *testing.T) {

				if len(blindAlerter.alerts) <= i {
					t.Fatalf("alert %d was not scheduled %v", i, blindAlerter.alerts)
				}

				alert := blindAlerter.alerts[i]

				amountGot := alert.amount
				if amountGot != c.expectedAmount {
					t.Errorf("got amount %d, want %d", amountGot, c.expectedAmount)
				}

				gotScheduledTime := alert.scheduledAt
				if gotScheduledTime != c.expectedScheduleTime {
					t.Errorf("got scheduled time of %v, want %v", gotScheduledTime, c.expectedScheduleTime)
				}
			})
		}
	})
```

يعمل الاختبار الجدولي جيداً هنا ويوضح بجلاء ما هي متطلباتنا. فنحن نمر على الجدول ونتحقق من `SpyBlindAlerter` لنرى إن كان التنبيه قد جُدول بالقيم الصحيحة.

## حاول تشغيل الاختبار

ينبغي أن تظهر لك حالات فشل كثيرة تبدو هكذا

```
=== RUN   TestCLI
--- FAIL: TestCLI (0.00s)
=== RUN   TestCLI/it_schedules_printing_of_blind_values
    --- FAIL: TestCLI/it_schedules_printing_of_blind_values (0.00s)
=== RUN   TestCLI/it_schedules_printing_of_blind_values/100_scheduled_for_0s
        --- FAIL: TestCLI/it_schedules_printing_of_blind_values/100_scheduled_for_0s (0.00s)
        	CLI_test.go:71: got scheduled time of 5s, want 0s
=== RUN   TestCLI/it_schedules_printing_of_blind_values/200_scheduled_for_10m0s
        --- FAIL: TestCLI/it_schedules_printing_of_blind_values/200_scheduled_for_10m0s (0.00s)
        	CLI_test.go:59: alert 1 was not scheduled [{5000000000 100}]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (cli *CLI) PlayPoker() {

	blinds := []int{100, 200, 300, 400, 500, 600, 800, 1000, 2000, 4000, 8000}
	blindTime := 0 * time.Second
	for _, blind := range blinds {
		cli.alerter.ScheduleAlertAt(blindTime, blind)
		blindTime = blindTime + 10*time.Minute
	}

	userInput := cli.readLine()
	cli.playerStore.RecordWin(extractWinner(userInput))
}
```

ليس هذا أعقد بكثير مما كان لدينا. فكل ما في الأمر أننا نمر الآن على مصفوفة `blinds` ونستدعي المجدوِل بقيمة `blindTime` متزايدة

## أعد الهيكلة

يمكننا تغليف تنبيهاتنا المجدولة في طريقة لمجرد جعل `PlayPoker` أوضح قراءة قليلاً.

```go
func (cli *CLI) PlayPoker() {
	cli.scheduleBlindAlerts()
	userInput := cli.readLine()
	cli.playerStore.RecordWin(extractWinner(userInput))
}

func (cli *CLI) scheduleBlindAlerts() {
	blinds := []int{100, 200, 300, 400, 500, 600, 800, 1000, 2000, 4000, 8000}
	blindTime := 0 * time.Second
	for _, blind := range blinds {
		cli.alerter.ScheduleAlertAt(blindTime, blind)
		blindTime = blindTime + 10*time.Minute
	}
}
```

أخيراً، تبدو اختباراتنا ثقيلة بعض الشيء. فلدينا بنيتان مجهولتان تمثلان الشيء نفسه، أي `ScheduledAlert`. لنُعِد هيكلة ذلك في نوع (type) جديد، ثم ننشئ بعض الدوال المساعدة لمقارنتها.

```go
type scheduledAlert struct {
	at     time.Duration
	amount int
}

func (s scheduledAlert) String() string {
	return fmt.Sprintf("%d chips at %v", s.amount, s.at)
}

type SpyBlindAlerter struct {
	alerts []scheduledAlert
}

func (s *SpyBlindAlerter) ScheduleAlertAt(at time.Duration, amount int) {
	s.alerts = append(s.alerts, scheduledAlert{at, amount})
}
```

أضفنا الطريقة `String()` إلى نوعنا كي يُطبع بشكل جميل إن فشل الاختبار

حدّث اختبارنا ليستعمل النوع الجديد

```go
t.Run("it schedules printing of blind values", func(t *testing.T) {
	in := strings.NewReader("Chris wins\n")
	playerStore := &poker.StubPlayerStore{}
	blindAlerter := &SpyBlindAlerter{}

	cli := poker.NewCLI(playerStore, in, blindAlerter)
	cli.PlayPoker()

	cases := []scheduledAlert{
		{0 * time.Second, 100},
		{10 * time.Minute, 200},
		{20 * time.Minute, 300},
		{30 * time.Minute, 400},
		{40 * time.Minute, 500},
		{50 * time.Minute, 600},
		{60 * time.Minute, 800},
		{70 * time.Minute, 1000},
		{80 * time.Minute, 2000},
		{90 * time.Minute, 4000},
		{100 * time.Minute, 8000},
	}

	for i, want := range cases {
		t.Run(fmt.Sprint(want), func(t *testing.T) {

			if len(blindAlerter.alerts) <= i {
				t.Fatalf("alert %d was not scheduled %v", i, blindAlerter.alerts)
			}

			got := blindAlerter.alerts[i]
			assertScheduledAlert(t, got, want)
		})
	}
})
```

نفّذ `assertScheduledAlert` بنفسك.

قضينا وقتاً لا بأس به هنا في كتابة الاختبارات، وكنا مشاغبين بعض الشيء بعدم الدمج مع تطبيقنا. لنعالج ذلك قبل أن نكدّس مزيداً من المتطلبات.

حاول تشغيل التطبيق، فلن يُصرَّف، معترضاً على عدم كفاية الوسطاء الممررة إلى `NewCLI`.

لننشئ تنفيذاً لـ`BlindAlerter` يمكننا استعماله في تطبيقنا.

أنشئ `blind_alerter.go` وانقل إليه الواجهة `BlindAlerter`، وأضف الأشياء الجديدة أدناه

```go
package poker

import (
	"fmt"
	"os"
	"time"
)

type BlindAlerter interface {
	ScheduleAlertAt(duration time.Duration, amount int)
}

type BlindAlerterFunc func(duration time.Duration, amount int)

func (a BlindAlerterFunc) ScheduleAlertAt(duration time.Duration, amount int) {
	a(duration, amount)
}

func StdOutAlerter(duration time.Duration, amount int) {
	time.AfterFunc(duration, func() {
		fmt.Fprintf(os.Stdout, "Blind is now %d\n", amount)
	})
}
```

تذكّر أن أي _نوع_ يمكنه تحقيق واجهة، لا البنى `structs` فقط. فإن كنت تصنع مكتبة تكشف واجهة عُرّفت فيها دالة واحدة، فمن الأساليب الشائعة أن تكشف أيضاً نوعاً مثل `MyInterfaceFunc`.

سيكون هذا النوع `func` يحقق واجهتك أيضاً. وبهذا يكون لمستخدمي واجهتك خيار تحقيقها بدالة فقط، بدلاً من الاضطرار إلى إنشاء نوع `struct` فارغ.

ثم ننشئ الدالة `StdOutAlerter` التي لها التوقيع نفسه، ونستعمل فقط `time.AfterFunc` لجدولتها لتطبع إلى `os.Stdout`.

حدّث `main` حيث ننشئ `NewCLI` لترى هذا عملياً

```go
poker.NewCLI(store, os.Stdin, poker.BlindAlerterFunc(poker.StdOutAlerter)).PlayPoker()
```

قبل التشغيل، قد ترغب في تغيير زيادة `blindTime` في `CLI` لتكون 10 ثوانٍ بدلاً من 10 دقائق، لمجرد أن ترى ذلك عملياً.

ينبغي أن تراه يطبع قيم الرهان الأعمى كما نتوقع كل 10 ثوانٍ. ولاحظ أنك ما زلت تستطيع كتابة `Shaun wins` في واجهة سطر الأوامر، فيوقف البرنامج كما نتوقع.

لن تُلعب اللعبة دائماً مع 5 أشخاص، لذا علينا أن نطلب من المستخدم إدخال عدد اللاعبين قبل بدء اللعبة.

## اكتب الاختبار أولاً

للتحقق من أننا نطلب عدد اللاعبين، سنريد تسجيل ما يُكتب إلى `StdOut`. فعلنا هذا بضع مرات من قبل، ونعرف أن `os.Stdout` هو `io.Writer`، لذا يمكننا التحقق مما يُكتب إن استعملنا حقن التبعية (dependency injection) لتمرير `bytes.Buffer` في اختبارنا، ورؤية ما ستكتبه شيفرتنا.

لا نهتم بالمتعاونين الآخرين في هذا الاختبار بعد، لذا صنعنا بعض الدمى في ملف الاختبار.

ينبغي أن نكون حذرين قليلاً من أن لدى `CLI` الآن 4 تبعيات، وهذا يبدو وكأنه بدأ يحمل مسؤوليات أكثر من اللازم. لنتعايش مع ذلك الآن، ونرى إن ظهرت إعادة هيكلة ونحن نضيف هذه الوظيفة الجديدة.

```go
var dummyBlindAlerter = &SpyBlindAlerter{}
var dummyPlayerStore = &poker.StubPlayerStore{}
var dummyStdIn = &bytes.Buffer{}
var dummyStdOut = &bytes.Buffer{}
```

إليك اختبارنا الجديد

```go
t.Run("it prompts the user to enter the number of players", func(t *testing.T) {
	stdout := &bytes.Buffer{}
	cli := poker.NewCLI(dummyPlayerStore, dummyStdIn, stdout, dummyBlindAlerter)
	cli.PlayPoker()

	got := stdout.String()
	want := "Please enter the number of players: "

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}
})
```

نمرر ما سيكون `os.Stdout` في `main`، ونرى ما يُكتب.

## حاول تشغيل الاختبار

```
./CLI_test.go:38:27: too many arguments in call to poker.NewCLI
	have (*poker.StubPlayerStore, *bytes.Buffer, *bytes.Buffer, *SpyBlindAlerter)
	want (poker.PlayerStore, io.Reader, poker.BlindAlerter)
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

لدينا تبعية جديدة، لذا سنضطر إلى تحديث `NewCLI`

```go
func NewCLI(store PlayerStore, in io.Reader, out io.Writer, alerter BlindAlerter) *CLI
```

والآن ستفشل الاختبارات _الأخرى_ في التصريف لأنها لا تمرر `io.Writer` إلى `NewCLI`.

أضف `dummyStdOut` للاختبارات الأخرى.

ينبغي أن يفشل الاختبار الجديد هكذا

```
=== RUN   TestCLI
--- FAIL: TestCLI (0.00s)
=== RUN   TestCLI/it_prompts_the_user_to_enter_the_number_of_players
    --- FAIL: TestCLI/it_prompts_the_user_to_enter_the_number_of_players (0.00s)
    	CLI_test.go:46: got '', want 'Please enter the number of players: '
FAIL
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

علينا إضافة تبعيتنا الجديدة إلى `CLI` كي نستطيع الإشارة إليها في `PlayPoker`

```go
type CLI struct {
	playerStore PlayerStore
	in          *bufio.Scanner
	out         io.Writer
	alerter     BlindAlerter
}

func NewCLI(store PlayerStore, in io.Reader, out io.Writer, alerter BlindAlerter) *CLI {
	return &CLI{
		playerStore: store,
		in:          bufio.NewScanner(in),
		out:         out,
		alerter:     alerter,
	}
}
```

ثم أخيراً يمكننا كتابة طلب الإدخال في بداية اللعبة

```go
func (cli *CLI) PlayPoker() {
	fmt.Fprint(cli.out, "Please enter the number of players: ")
	cli.scheduleBlindAlerts()
	userInput := cli.readLine()
	cli.playerStore.RecordWin(extractWinner(userInput))
}
```

## أعد الهيكلة

لدينا سلسلة نصية مكررة لطلب الإدخال، ينبغي أن نستخرجها إلى ثابت (constant)

```go
const PlayerPrompt = "Please enter the number of players: "
```

استعمل هذا في شيفرة الاختبار وفي `CLI` كليهما.

والآن علينا إرسال عدد واستخراجه. والطريقة الوحيدة لنعرف إن كان له الأثر المطلوب هي رؤية تنبيهات الرهان الأعمى التي جُدولت.

## اكتب الاختبار أولاً

```go
t.Run("it prompts the user to enter the number of players", func(t *testing.T) {
	stdout := &bytes.Buffer{}
	in := strings.NewReader("7\n")
	blindAlerter := &SpyBlindAlerter{}

	cli := poker.NewCLI(dummyPlayerStore, in, stdout, blindAlerter)
	cli.PlayPoker()

	got := stdout.String()
	want := poker.PlayerPrompt

	if got != want {
		t.Errorf("got %q, want %q", got, want)
	}

	cases := []scheduledAlert{
		{0 * time.Second, 100},
		{12 * time.Minute, 200},
		{24 * time.Minute, 300},
		{36 * time.Minute, 400},
	}

	for i, want := range cases {
		t.Run(fmt.Sprint(want), func(t *testing.T) {

			if len(blindAlerter.alerts) <= i {
				t.Fatalf("alert %d was not scheduled %v", i, blindAlerter.alerts)
			}

			got := blindAlerter.alerts[i]
			assertScheduledAlert(t, got, want)
		})
	}
})
```

آخ! تغييرات كثيرة.

- نزيل الدمية الخاصة بـ`StdIn`، ونرسل بدلاً منها نسخة وهمية تمثل مستخدمنا وهو يُدخل 7
- ونزيل أيضاً الدمية الخاصة بمنبّه الرهان الأعمى كي نرى أن عدد اللاعبين قد أثّر في الجدولة
- نختبر التنبيهات التي جُدولت

## حاول تشغيل الاختبار

ينبغي أن يظل الاختبار يُصرَّف وأن يفشل، مبلّغاً بأن الأوقات المجدولة خاطئة، لأننا ثبّتنا في الشيفرة أن اللعبة مبنية على وجود 5 لاعبين

```
=== RUN   TestCLI
--- FAIL: TestCLI (0.00s)
=== RUN   TestCLI/it_prompts_the_user_to_enter_the_number_of_players
    --- FAIL: TestCLI/it_prompts_the_user_to_enter_the_number_of_players (0.00s)
=== RUN   TestCLI/it_prompts_the_user_to_enter_the_number_of_players/100_chips_at_0s
        --- PASS: TestCLI/it_prompts_the_user_to_enter_the_number_of_players/100_chips_at_0s (0.00s)
=== RUN   TestCLI/it_prompts_the_user_to_enter_the_number_of_players/200_chips_at_12m0s
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

تذكّر أننا أحرار في ارتكاب ما نحتاج إليه من خطايا لجعل هذا يعمل. وبمجرد أن يكون لدينا برنامج يعمل، يمكننا العمل على إعادة هيكلة الفوضى التي نوشك أن نُحدثها!

```go
func (cli *CLI) PlayPoker() {
	fmt.Fprint(cli.out, PlayerPrompt)

	numberOfPlayers, _ := strconv.Atoi(cli.readLine())

	cli.scheduleBlindAlerts(numberOfPlayers)

	userInput := cli.readLine()
	cli.playerStore.RecordWin(extractWinner(userInput))
}

func (cli *CLI) scheduleBlindAlerts(numberOfPlayers int) {
	blindIncrement := time.Duration(5+numberOfPlayers) * time.Minute

	blinds := []int{100, 200, 300, 400, 500, 600, 800, 1000, 2000, 4000, 8000}
	blindTime := 0 * time.Second
	for _, blind := range blinds {
		cli.alerter.ScheduleAlertAt(blindTime, blind)
		blindTime = blindTime + blindIncrement
	}
}
```

- نقرأ `numberOfPlayersInput` في سلسلة نصية
- نستعمل `cli.readLine()` للحصول على مدخلات المستخدم، ثم نستدعي `Atoi` لتحويلها إلى عدد صحيح، متجاهلين أي سيناريوهات خطأ. وسنحتاج إلى كتابة اختبار لذلك السيناريو لاحقاً.
- ومن هنا نغيّر `scheduleBlindAlerts` لتقبل عدد اللاعبين. ثم نحسب وقت `blindIncrement` نستعمله للإضافة إلى `blindTime` ونحن نمر على مقادير الرهان الأعمى

مع أن اختبارنا الجديد قد أُصلح، فقد فشلت اختبارات كثيرة أخرى، لأن نظامنا صار لا يعمل إلا إن بدأت اللعبة بإدخال المستخدم عدداً. وستحتاج إلى إصلاح الاختبارات بتغيير مدخلات المستخدم بحيث يُضاف عدد يليه سطر جديد (وهذا يكشف مزيداً من العيوب في أسلوبنا الحالي).

## أعد الهيكلة

يبدو كل هذا فظيعاً بعض الشيء، أليس كذلك؟ لـ**نصغِ إلى اختباراتنا**.

- لكي نختبر أننا نجدول بعض التنبيهات، أعددنا 4 تبعيات مختلفة. وكلما كانت لديك تبعيات كثيرة لـ_شيء_ ما في نظامك، فهذا يعني أنه يفعل أكثر من اللازم. ويمكننا أن نرى ذلك بصرياً في مدى ازدحام اختبارنا.
- يبدو لي أننا **نحتاج إلى تجريد أنظف بين قراءة مدخلات المستخدم ومنطق الأعمال الذي نريد تنفيذه**
- سيكون الاختبار الأفضل: _بمعلومية مدخلات المستخدم هذه، هل نستدعي نوعاً جديداً `Game` بعدد اللاعبين الصحيح؟_
- ثم سننقل اختبار الجدولة إلى اختبارات النوع الجديد `Game`.

يمكننا إعادة الهيكلة نحو `Game` أولاً، وينبغي أن يظل اختبارنا ناجحاً. وبمجرد أن نجري التغييرات البنيوية التي نريدها، يمكننا التفكير في كيفية إعادة هيكلة الاختبارات لتعكس فصل الاهتمامات الجديد

وتذكّر عند إجراء التغييرات في إعادة الهيكلة أن تحاول إبقاءها صغيرة قدر الإمكان، وأن تواصل إعادة تشغيل الاختبارات.

جرّبه بنفسك أولاً. فكّر في حدود ما سيقدمه `Game` وما ينبغي أن يفعله `CLI`.

في الوقت الحالي **لا** تغيّر الواجهة الخارجية لـ`NewCLI`، لأننا لا نريد تغيير شيفرة الاختبار وشيفرة العميل في الوقت نفسه، فهذا أكثر من اللازم، وقد ينتهي بنا الأمر إلى إفساد الأشياء.

هذا ما توصلت إليه:

```go
// game.go
type Game struct {
	alerter BlindAlerter
	store   PlayerStore
}

func (p *Game) Start(numberOfPlayers int) {
	blindIncrement := time.Duration(5+numberOfPlayers) * time.Minute

	blinds := []int{100, 200, 300, 400, 500, 600, 800, 1000, 2000, 4000, 8000}
	blindTime := 0 * time.Second
	for _, blind := range blinds {
		p.alerter.ScheduleAlertAt(blindTime, blind)
		blindTime = blindTime + blindIncrement
	}
}

func (p *Game) Finish(winner string) {
	p.store.RecordWin(winner)
}

// cli.go
type CLI struct {
	in   *bufio.Scanner
	out  io.Writer
	game *Game
}

func NewCLI(store PlayerStore, in io.Reader, out io.Writer, alerter BlindAlerter) *CLI {
	return &CLI{
		in:  bufio.NewScanner(in),
		out: out,
		game: &Game{
			alerter: alerter,
			store:   store,
		},
	}
}

const PlayerPrompt = "Please enter the number of players: "

func (cli *CLI) PlayPoker() {
	fmt.Fprint(cli.out, PlayerPrompt)

	numberOfPlayersInput := cli.readLine()
	numberOfPlayers, _ := strconv.Atoi(strings.Trim(numberOfPlayersInput, "\n"))

	cli.game.Start(numberOfPlayers)

	winnerInput := cli.readLine()
	winner := extractWinner(winnerInput)

	cli.game.Finish(winner)
}

func extractWinner(userInput string) string {
	return strings.Replace(userInput, " wins\n", "", 1)
}

func (cli *CLI) readLine() string {
	cli.in.Scan()
	return cli.in.Text()
}
```

من منظور "المجال":
- نريد أن نبدأ `Game` بـ`Start`، مع تحديد عدد اللاعبين
- ونريد أن ننهي `Game` بـ`Finish`، مع إعلان الفائز

ويغلّف النوع الجديد `Game` هذا لنا.

بهذا التغيير مررنا `BlindAlerter` و`PlayerStore` إلى `Game`، لأنه صار مسؤولاً الآن عن التنبيه وتخزين النتائج.

صار `CLI` يهتم الآن فقط بـ:

- بناء `Game` بتبعياته الحالية (وهو ما سنعيد هيكلته بعد ذلك)
- تفسير مدخلات المستخدم كاستدعاءات لطرق `Game`

نريد محاولة تجنب عمليات إعادة الهيكلة "الكبيرة" التي تتركنا في حالة اختبارات فاشلة لفترات طويلة، لأن ذلك يزيد احتمالات الأخطاء. (وإن كنت تعمل في فريق كبير أو موزع، فهذا أهم بكثير)

أول ما سنفعله هو إعادة هيكلة `Game` بحيث نحقنه في `CLI`. وسنجري أصغر التغييرات في اختباراتنا لتسهيل ذلك، ثم سنرى كيف يمكننا تقسيم الاختبارات إلى موضوعي تحليل مدخلات المستخدم وإدارة اللعبة.

كل ما علينا فعله الآن هو تغيير `NewCLI`

```go
func NewCLI(in io.Reader, out io.Writer, game *Game) *CLI {
	return &CLI{
		in:   bufio.NewScanner(in),
		out:  out,
		game: game,
	}
}
```

يبدو هذا تحسيناً بالفعل. فلدينا تبعيات أقل، و_قائمة تبعياتنا تعكس هدفنا التصميمي العام_ في أن يهتم `CLI` بالإدخال والإخراج ويفوّض الإجراءات الخاصة باللعبة إلى `Game`.

إن حاولت التصريف فستجد مشكلات. وينبغي أن تستطيع إصلاحها بنفسك. لا تقلق بشأن صنع أي بدائل وهمية لـ`Game` الآن، بل هيّئ قيم `Game` _حقيقية_ فقط لجعل كل شيء يُصرَّف والاختبارات خضراء.

لفعل ذلك ستحتاج إلى صنع دالة بانية

```go
func NewGame(alerter BlindAlerter, store PlayerStore) *Game {
	return &Game{
		alerter: alerter,
		store:   store,
	}
}
```

إليك مثالاً على أحد إعدادات الاختبارات بعد إصلاحه

```go
stdout := &bytes.Buffer{}
in := strings.NewReader("7\n")
blindAlerter := &SpyBlindAlerter{}
game := poker.NewGame(blindAlerter, dummyPlayerStore)

cli := poker.NewCLI(in, stdout, game)
cli.PlayPoker()
```

لا ينبغي أن يتطلب إصلاح الاختبارات والعودة إلى الأخضر جهداً كبيراً (وهذا هو المقصود!)، لكن تأكد من إصلاح `main.go` أيضاً قبل المرحلة التالية.

```go
// main.go
game := poker.NewGame(poker.BlindAlerterFunc(poker.StdOutAlerter), store)
cli := poker.NewCLI(os.Stdin, os.Stdout, game)
cli.PlayPoker()
```

والآن بعد أن استخرجنا `Game`، ينبغي أن ننقل التوكيدات الخاصة باللعبة إلى اختبارات منفصلة عن `CLI`.

وهذا مجرد تمرين في نسخ اختبارات `CLI` لكن بتبعيات أقل

```go
func TestGame_Start(t *testing.T) {
	t.Run("schedules alerts on game start for 5 players", func(t *testing.T) {
		blindAlerter := &poker.SpyBlindAlerter{}
		game := poker.NewGame(blindAlerter, dummyPlayerStore)

		game.Start(5)

		cases := []poker.ScheduledAlert{
			{At: 0 * time.Second, Amount: 100},
			{At: 10 * time.Minute, Amount: 200},
			{At: 20 * time.Minute, Amount: 300},
			{At: 30 * time.Minute, Amount: 400},
			{At: 40 * time.Minute, Amount: 500},
			{At: 50 * time.Minute, Amount: 600},
			{At: 60 * time.Minute, Amount: 800},
			{At: 70 * time.Minute, Amount: 1000},
			{At: 80 * time.Minute, Amount: 2000},
			{At: 90 * time.Minute, Amount: 4000},
			{At: 100 * time.Minute, Amount: 8000},
		}

		checkSchedulingCases(cases, t, blindAlerter)
	})

	t.Run("schedules alerts on game start for 7 players", func(t *testing.T) {
		blindAlerter := &poker.SpyBlindAlerter{}
		game := poker.NewGame(blindAlerter, dummyPlayerStore)

		game.Start(7)

		cases := []poker.ScheduledAlert{
			{At: 0 * time.Second, Amount: 100},
			{At: 12 * time.Minute, Amount: 200},
			{At: 24 * time.Minute, Amount: 300},
			{At: 36 * time.Minute, Amount: 400},
		}

		checkSchedulingCases(cases, t, blindAlerter)
	})

}

func TestGame_Finish(t *testing.T) {
	store := &poker.StubPlayerStore{}
	game := poker.NewGame(dummyBlindAlerter, store)
	winner := "Ruth"

	game.Finish(winner)
	poker.AssertPlayerWin(t, store, winner)
}
```

صار القصد مما يحدث حين تبدأ لعبة بوكر أوضح بكثير الآن.

تأكد من نقل اختبار انتهاء اللعبة أيضاً.

وبمجرد أن نرضى بأننا نقلنا اختبارات منطق اللعبة، يمكننا تبسيط اختبارات `CLI` لتعكس المسؤوليات المقصودة بوضوح أكبر

- معالجة مدخلات المستخدم واستدعاء طرق `Game` عند الحاجة
- إرسال المخرجات
- والأهم أنه لا يعرف شيئاً عن طريقة عمل الألعاب الفعلية

لفعل ذلك، علينا جعل `CLI` لا يعتمد بعد الآن على النوع الملموس `Game`، بل يقبل واجهة فيها `Start(numberOfPlayers)` و`Finish(winner)`. ثم يمكننا إنشاء جاسوس من ذلك النوع والتحقق من أن الاستدعاءات الصحيحة تتم.

وهنا ندرك أن التسمية تكون محرجة أحياناً. غيّر اسم `Game` إلى `TexasHoldem` (لأن هذا هو _نوع_ اللعبة التي نلعبها)، وستسمى الواجهة الجديدة `Game`. وهذا يبقى وفياً لفكرة أن `CLI` لا يدري باللعبة الفعلية التي نلعبها ولا بما يحدث حين تستدعي `Start` و`Finish`.

```go
type Game interface {
	Start(numberOfPlayers int)
	Finish(winner string)
}
```

استبدل كل الإشارات إلى `*Game` داخل `CLI` بـ`Game` (واجهتنا الجديدة). وكالعادة، واصل إعادة تشغيل الاختبارات للتحقق من أن كل شيء أخضر ونحن نعيد الهيكلة.

والآن بعد أن فككنا الاقتران بين `CLI` و`TexasHoldem`، يمكننا استعمال الجواسيس للتحقق من أن `Start` و`Finish` تُستدعيان حين نتوقع، بالوسطاء الصحيحة.

أنشئ جاسوساً يحقق `Game`

```go
type GameSpy struct {
	StartedWith  int
	FinishedWith string
}

func (g *GameSpy) Start(numberOfPlayers int) {
	g.StartedWith = numberOfPlayers
}

func (g *GameSpy) Finish(winner string) {
	g.FinishedWith = winner
}
```

استبدل أي اختبار لـ`CLI` يختبر منطقاً خاصاً باللعبة بفحوص على كيفية استدعاء `GameSpy`. وهذا سيعكس بعد ذلك مسؤوليات `CLI` في اختباراتنا بوضوح.

إليك مثالاً على أحد الاختبارات بعد إصلاحه؛ حاول أن تفعل البقية بنفسك، وراجع الشيفرة المصدرية إن علقت.

```go
	t.Run("it prompts the user to enter the number of players and starts the game", func(t *testing.T) {
		stdout := &bytes.Buffer{}
		in := strings.NewReader("7\n")
		game := &GameSpy{}

		cli := poker.NewCLI(in, stdout, game)
		cli.PlayPoker()

		gotPrompt := stdout.String()
		wantPrompt := poker.PlayerPrompt

		if gotPrompt != wantPrompt {
			t.Errorf("got %q, want %q", gotPrompt, wantPrompt)
		}

		if game.StartedWith != 7 {
			t.Errorf("wanted Start called with 7 but got %d", game.StartedWith)
		}
	})
```

والآن بعد أن صار لدينا فصل نظيف للاهتمامات، ينبغي أن يكون التحقق من الحالات الحدّية المتعلقة بالإدخال والإخراج في `CLI` أسهل.

علينا معالجة السيناريو الذي يُدخل فيه المستخدم قيمة غير عددية حين يُطلب منه عدد اللاعبين:

لا ينبغي أن تبدأ شيفرتنا اللعبة، وينبغي أن تطبع خطأً مفيداً للمستخدم ثم تنتهي.

## اكتب الاختبار أولاً

سنبدأ بالتأكد من أن اللعبة لا تبدأ

```go
t.Run("it prints an error when a non numeric value is entered and does not start the game", func(t *testing.T) {
	stdout := &bytes.Buffer{}
	in := strings.NewReader("Pies\n")
	game := &GameSpy{}

	cli := poker.NewCLI(in, stdout, game)
	cli.PlayPoker()

	if game.StartCalled {
		t.Errorf("game should not have started")
	}
})
```

ستحتاج إلى إضافة حقل `StartCalled` إلى `GameSpy`، لا يُضبط إلا إن استُدعيت `Start`

## حاول تشغيل الاختبار

```
=== RUN   TestCLI/it_prints_an_error_when_a_non_numeric_value_is_entered_and_does_not_start_the_game
    --- FAIL: TestCLI/it_prints_an_error_when_a_non_numeric_value_is_entered_and_does_not_start_the_game (0.00s)
        CLI_test.go:62: game should not have started
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

حول الموضع الذي نستدعي فيه `Atoi` علينا فقط التحقق من الخطأ (error)

```go
numberOfPlayers, err := strconv.Atoi(cli.readLine())

if err != nil {
	return
}
```

بعد ذلك علينا إبلاغ المستخدم بما أخطأ فيه، لذا سنؤكد على ما يُطبع إلى `stdout`.

## اكتب الاختبار أولاً

أكدنا على ما طُبع إلى `stdout` من قبل، لذا يمكننا نسخ تلك الشيفرة في الوقت الحالي

```go
gotPrompt := stdout.String()

wantPrompt := poker.PlayerPrompt + "you're so silly"

if gotPrompt != wantPrompt {
	t.Errorf("got %q, want %q", gotPrompt, wantPrompt)
}
```

نحن نخزّن _كل_ ما يُكتب إلى `stdout`، لذا ما زلنا نتوقع `poker.PlayerPrompt`. ثم نتحقق فقط من طباعة شيء إضافي. ولا نهتم كثيراً بالصياغة الدقيقة الآن، وسنعالجها حين نعيد الهيكلة.

## حاول تشغيل الاختبار

```
=== RUN   TestCLI/it_prints_an_error_when_a_non_numeric_value_is_entered_and_does_not_start_the_game
    --- FAIL: TestCLI/it_prints_an_error_when_a_non_numeric_value_is_entered_and_does_not_start_the_game (0.00s)
        CLI_test.go:70: got 'Please enter the number of players: ', want 'Please enter the number of players: you're so silly'
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

غيّر شيفرة معالجة الأخطاء

```go
if err != nil {
	fmt.Fprint(cli.out, "you're so silly")
	return
}
```

## أعد الهيكلة

أعد هيكلة الرسالة الآن إلى ثابت مثل `PlayerPrompt`

```go
wantPrompt := poker.PlayerPrompt + poker.BadPlayerInputErrMsg
```

وضع رسالة أنسب

```go
const BadPlayerInputErrMsg = "Bad value received for number of players, please try again with a number"
```

وأخيراً، اختباراتنا حول ما أُرسل إلى `stdout` مسهبة إلى حد ما، فلنكتب دالة توكيد لتنظيفها.

```go
func assertMessagesSentToUser(t testing.TB, stdout *bytes.Buffer, messages ...string) {
	t.Helper()
	want := strings.Join(messages, "")
	got := stdout.String()
	if got != want {
		t.Errorf("got %q sent to stdout but expected %+v", got, messages)
	}
}
```

استعمال صياغة الوسطاء المتغيرة (`...string`) مفيد هنا، لأننا نحتاج إلى التوكيد على أعداد متفاوتة من الرسائل.

استعمل هذه الدالة المساعدة في الاختبارين اللذين نؤكد فيهما على الرسائل المرسلة إلى المستخدم.

هناك عدد من الاختبارات التي يمكن أن تستفيد من بعض دوال `assertX`، فتمرّن على إعادة الهيكلة بتنظيف اختباراتنا لتُقرأ بشكل جميل.

خذ بعض الوقت وفكّر في قيمة بعض الاختبارات التي استخلصناها. وتذكّر أننا لا نريد اختبارات أكثر من اللازم، فهل تستطيع إعادة هيكلة بعضها أو حذفه _مع الاحتفاظ بالثقة بأن كل شيء يعمل_؟

هذا ما توصلت إليه

```go
func TestCLI(t *testing.T) {

	t.Run("start game with 3 players and finish game with 'Chris' as winner", func(t *testing.T) {
		game := &GameSpy{}
		stdout := &bytes.Buffer{}

		in := userSends("3", "Chris wins")
		cli := poker.NewCLI(in, stdout, game)

		cli.PlayPoker()

		assertMessagesSentToUser(t, stdout, poker.PlayerPrompt)
		assertGameStartedWith(t, game, 3)
		assertFinishCalledWith(t, game, "Chris")
	})

	t.Run("start game with 8 players and record 'Cleo' as winner", func(t *testing.T) {
		game := &GameSpy{}

		in := userSends("8", "Cleo wins")
		cli := poker.NewCLI(in, dummyStdOut, game)

		cli.PlayPoker()

		assertGameStartedWith(t, game, 8)
		assertFinishCalledWith(t, game, "Cleo")
	})

	t.Run("it prints an error when a non numeric value is entered and does not start the game", func(t *testing.T) {
		game := &GameSpy{}

		stdout := &bytes.Buffer{}
		in := userSends("pies")

		cli := poker.NewCLI(in, stdout, game)
		cli.PlayPoker()

		assertGameNotStarted(t, game)
		assertMessagesSentToUser(t, stdout, poker.PlayerPrompt, poker.BadPlayerInputErrMsg)
	})
}
```
تعكس الاختبارات الآن القدرات الأساسية لـ`CLI`، فهو يستطيع قراءة مدخلات المستخدم فيما يخص عدد اللاعبين ومن فاز، ويتعامل مع إدخال قيمة سيئة لعدد اللاعبين. وبهذا يتضح للقارئ ما يفعله `CLI`، وأيضاً ما لا يفعله.

ماذا يحدث إن كتب المستخدم `Lloyd is a killer` بدلاً من `Ruth wins`؟

اختم هذا الفصل بكتابة اختبار لهذا السيناريو وجعله ينجح.

## الخلاصة

### ملخص سريع للمشروع

في الفصول الخمسة الماضية بنينا تدريجياً بـ`TDD` قدراً لا بأس به من الشيفرة

- لدينا تطبيقان: تطبيق سطر أوامر وخادم ويب.
- يعتمد كلا التطبيقين على `PlayerStore` لتسجيل الفائزين
- يستطيع خادم الويب أيضاً عرض جدول دوري بمن يفوز بأكبر عدد من المباريات
- يساعد تطبيق سطر الأوامر اللاعبين على لعب البوكر بتتبع قيمة الرهان الأعمى الحالية.

### الدالة `time.Afterfunc`

وسيلة مفيدة جداً لجدولة استدعاء دالة بعد مدة محددة. ويستحق الأمر حقاً استثمار الوقت في [الاطلاع على توثيق الحزمة `time`](https://golang.org/pkg/time/)، ففيها كثير من الدوال والطرق الموفرة للوقت لتعمل معها.

ومن المفضلة لدي

- تعيد `time.After(duration)` قيمة `chan Time` حين تنقضي المدة. فإن أردت فعل شيء ما _بعد_ وقت محدد، فقد يساعدك هذا.
- تعيد `time.NewTicker(duration)` قيمة `Ticker`، وهي تشبه ما سبق في أنها تعيد قناة، لكن هذه "تدق" مع كل مدة، لا مرة واحدة فقط. وهذا مفيد جداً إن أردت تنفيذ شيفرة ما كل `N duration`.

### مزيد من الأمثلة على الفصل الجيد للاهتمامات

من الممارسات الجيدة _عموماً_ فصل مسؤوليات التعامل مع مدخلات المستخدم والردود عليه عن شيفرة المجال. وترى ذلك هنا في تطبيق سطر الأوامر وفي خادم الويب أيضاً.

صارت اختباراتنا فوضوية. فقد كانت لدينا توكيدات كثيرة جداً (تحقق من هذا المدخل، وجدول هذه التنبيهات، وغير ذلك) وتبعيات كثيرة جداً. وكنا نرى بصرياً أنها مزدحمة؛ ومن **المهم جداً أن تصغي إلى اختباراتك**.

- إن بدت اختباراتك فوضوية، فحاول إعادة هيكلتها.
- وإن فعلت ذلك وما زالت فوضوية، فالأرجح جداً أنها تشير إلى عيب في تصميمك
- وهذه إحدى نقاط القوة الحقيقية للاختبارات.

مع أن الاختبارات وشيفرة الإنتاج كانت مزدحمة بعض الشيء، استطعنا إعادة الهيكلة بحرية مدعومين باختباراتنا.

تذكّر حين تقع في هذه المواقف أن تتخذ دائماً خطوات صغيرة، وأن تعيد تشغيل الاختبارات بعد كل تغيير.

كان سيكون خطيراً أن نعيد هيكلة شيفرة الاختبار _و_ شيفرة الإنتاج في الوقت نفسه، لذا أعدنا هيكلة شيفرة الإنتاج أولاً (لم نكن نستطيع تحسين الاختبارات كثيراً في حالتها الراهنة) دون تغيير واجهتها، كي نعتمد على اختباراتنا قدر المستطاع ونحن نغيّر الأشياء. _ثم_ أعدنا هيكلة الاختبارات بعد أن تحسّن التصميم.

بعد إعادة الهيكلة صارت قائمة التبعيات تعكس هدفنا التصميمي. وهذه فائدة أخرى لحقن التبعية، إذ كثيراً ما يوثّق القصد. أما حين تعتمد على المتغيرات العامة، فتصبح المسؤوليات غير واضحة إطلاقاً.

## مثال على دالة تحقق واجهة

حين تعرّف واجهة فيها طريقة واحدة، قد ترغب في التفكير في تعريف نوع `MyInterfaceFunc` يكمّلها، كي يستطيع المستخدمون تحقيق واجهتك بدالة فقط.

```go
type BlindAlerter interface {
	ScheduleAlertAt(duration time.Duration, amount int)
}

// BlindAlerterFunc allows you to implement BlindAlerter with a function
type BlindAlerterFunc func(duration time.Duration, amount int)

// ScheduleAlertAt is BlindAlerterFunc implementation of BlindAlerter
func (a BlindAlerterFunc) ScheduleAlertAt(duration time.Duration, amount int) {
	a(duration, amount)
}
```

بفعل هذا، يستطيع مستعملو مكتبتك تحقيق واجهتك بدالة فقط. ويمكنهم استعمال [تحويل النوع](https://go.dev/tour/basics/13) لتحويل دالتهم إلى `BlindAlerterFunc`، ثم استعمالها كـ`BlindAlerter` (لأن `BlindAlerterFunc` يحقق `BlindAlerter`).

```go
game := poker.NewTexasHoldem(poker.BlindAlerterFunc(poker.StdOutAlerter), store)
```

والفكرة الأوسع هنا أنك في غو تستطيع إضافة طرق إلى _الأنواع_، لا البنى فقط. وهذه ميزة قوية جداً، ويمكنك استعمالها لتحقيق الواجهات بطرق أكثر ملاءمة.

وتذكّر أنك لا تستطيع تعريف أنواع للدوال فحسب، بل تستطيع أيضاً تعريف أنواع حول أنواع أخرى، كي تضيف إليها طرقاً.

```go
type Blog map[string]string

func (b Blog) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, b[r.URL.Path])
}
```

أنشأنا هنا معالج HTTP ينفّذ "مدونة" بسيطة جداً، يستعمل فيها مسارات URL مفاتيحَ للتدوينات المخزّنة في خريطة.
