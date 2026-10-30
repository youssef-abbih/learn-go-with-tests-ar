# سطر الأوامر وبنية المشروع

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/command-line)**

تريد مالكة المنتج الآن _تغيير الاتجاه_ بتقديم تطبيق ثانٍ، هو تطبيق سطر أوامر.

في الوقت الحالي، كل ما يحتاج إليه هو أن يستطيع تسجيل فوز لاعب حين يكتب المستخدم `Ruth wins`. والنية أن يصبح في النهاية أداة لمساعدة المستخدمين على لعب البوكر.

وتريد مالكة المنتج أن تكون قاعدة البيانات مشتركة بين التطبيقين، كي يتحدث الدوري بحسب مرات الفوز المسجلة في التطبيق الجديد.

## تذكير بالشيفرة

لدينا تطبيق فيه ملف `main.go` يشغّل خادم HTTP. لن يهمنا خادم HTTP في هذا التمرين، لكن التجريد الذي يستعمله سيهمنا. فهو يعتمد على `PlayerStore`.

```go
type PlayerStore interface {
	GetPlayerScore(name string) int
	RecordWin(name string)
	GetLeague() League
}
```

في الفصل السابق صنعنا `FileSystemPlayerStore` الذي يحقق تلك الواجهة (interface). وينبغي أن نستطيع إعادة استعمال شيء من ذلك في تطبيقنا الجديد.

## بعض إعادة الهيكلة للمشروع أولاً

صار مشروعنا يحتاج الآن إلى إنشاء ملفين تنفيذيين: خادم الويب الحالي وتطبيق سطر الأوامر.

وقبل أن نغوص في عملنا الجديد، ينبغي أن ننظم مشروعنا ليستوعب ذلك.

حتى الآن عاشت كل الشيفرة (code) في مجلد واحد، في مسار يبدو هكذا

`$GOPATH/src/github.com/your-name/my-app`

لكي تصنع تطبيقاً في غو (Go)، تحتاج إلى دالة `main` داخل `package main`. وحتى الآن عاشت كل شيفرة "المجال" لدينا داخل `package main`، وكانت `func main` تستطيع الإشارة إلى كل شيء.

كان هذا مقبولاً حتى الآن، ومن الممارسات الجيدة ألا تبالغ في بنية الحزم. فإن أخذت وقتك في تصفح المكتبة القياسية، فلن ترى إلا القليل من المجلدات الكثيرة والبنى المعقدة.

لحسن الحظ، إضافة البنية _حين تحتاج إليها_ أمر مباشر جداً.

داخل المشروع الحالي، أنشئ مجلداً `cmd` وداخله مجلد `webserver` (مثلاً `mkdir -p cmd/webserver`).

المجلد `cmd` اصطلاح واسع الانتشار في غو لحفظ حزم `main` الخاصة بالتطبيقات التي يبنيها المشروع، مع فصلها عن شيفرة المكتبة القابلة للاستيراد التي تعيش في جذر المشروع.

انقل `main.go` إلى داخله.

إن كانت الأداة `tree` مثبّتة لديك، فشغّلها، وينبغي أن تبدو بنيتك هكذا

```
.
|-- file_system_store.go
|-- file_system_store_test.go
|-- cmd
|   |-- webserver
|       |-- main.go
|-- league.go
|-- server.go
|-- server_integration_test.go
|-- server_test.go
|-- tape.go
|-- tape_test.go
```

صار لدينا الآن فعلياً فصل بين تطبيقنا وشيفرة المكتبة، لكن علينا الآن تغيير أسماء بعض الحزم. تذكّر أنه حين تبني تطبيق غو، _يجب_ أن تكون حزمته `main`.

غيّر كل الشيفرة الأخرى لتكون في حزمة (package) اسمها `poker`.

وأخيراً، علينا استيراد هذه الحزمة في `main.go` كي نستعملها لإنشاء خادم الويب. ثم يمكننا استعمال شيفرة المكتبة بكتابة `poker.FunctionName`.

ستكون المسارات مختلفة على حاسوبك، لكنها ينبغي أن تشبه هذا:

```go
// cmd/webserver/main.go
package main

import (
	"github.com/quii/learn-go-with-tests/command-line/v1"
	"log"
	"net/http"
	"os"
)

const dbFileName = "game.db.json"

func main() {
	db, err := os.OpenFile(dbFileName, os.O_RDWR|os.O_CREATE, 0666)

	if err != nil {
		log.Fatalf("problem opening %s %v", dbFileName, err)
	}

	store, err := poker.NewFileSystemPlayerStore(db)

	if err != nil {
		log.Fatalf("problem creating file system player store, %v ", err)
	}

	server := poker.NewPlayerServer(store)

	log.Fatal(http.ListenAndServe(":5000", server))
}
```

الثابت `dbFileName` مسار نسبي، لذا سيُنشأ الملف `game.db.json` (أو يُقرأ) نسبةً إلى المجلد الذي تشغّل _منه_ الملف التنفيذي الناتج، لا المجلد الذي يوجد فيه الملف التنفيذي. وبما أن مالك المنتج يريد أن يتشارك تطبيق سطر الأوامر وخادم الويب قاعدة البيانات نفسها، فهذا أمر مهم: فتشغيلهما من مجلدين مختلفين سيعطي كلاً منهما بصمت ملف `game.db.json` خاصاً به ومنفصلاً عن الآخر. وسنعود إلى هذا في قسم "الفحوص الأخيرة" أدناه.

قد يبدو المسار الكامل غريباً بعض الشيء، لكن هذه هي الطريقة التي تستطيع بها استيراد _أي_ مكتبة متاحة للعموم في شيفرتك.

بفصل شيفرة مجالنا في حزمة منفصلة وإيداعها في مستودع عام مثل GitHub، يستطيع أي مطور غو كتابة شيفرته الخاصة التي تستورد تلك الحزمة، فتصبح الميزات التي كتبناها متاحة له. وفي أول مرة تحاول تشغيلها ستعترض بأنها غير موجودة، لكن كل ما عليك هو تشغيل `go get`.

إضافة إلى ذلك، يستطيع المستخدمون عرض [التوثيق على pkg.go.dev](https://pkg.go.dev/github.com/quii/learn-go-with-tests/command-line/v1).

### الفحوص الأخيرة

- شغّل `go test` داخل الجذر وتحقق من أنها ما زالت تنجح
- ادخل إلى `cmd/webserver` ونفّذ `go run main.go`
  - زُر `http://localhost:5000/league` وينبغي أن ترى أنه ما زال يعمل

سنبني لاحقاً في هذا الفصل تطبيقاً ثانياً هو `cmd/cli`، ومن المفترض أن يتشارك الملف `game.db.json` نفسه مع خادم الويب. ولأن `dbFileName` يُحلّ نسبةً إلى مجلد العمل الحالي، ستحتاج إلى تشغيل الملفين التنفيذيين كليهما _من المجلد نفسه_ حتى يرى كل منهما تحديثات الآخر، كأن تبنيهما أولاً ثم تشغّل الملفين التنفيذيين من جذر المشروع (`go build -o webserver ./cmd/webserver && go build -o cli ./cmd/cli`، ثم `./webserver` و`./cli`)، بدلاً من استعمال `go run main.go` من داخل كل مجلد فرعي في `cmd`.

### الهيكل العظمي العامل

قبل أن نغوص في كتابة الاختبارات، لنُضِف تطبيقاً جديداً سيبنيه مشروعنا. أنشئ مجلداً آخر داخل `cmd` باسم `cli` (واجهة سطر الأوامر)، وأضف `main.go` بما يلي

```go
// cmd/cli/main.go
package main

import "fmt"

func main() {
	fmt.Println("Let's play poker")
}
```

أول متطلب سنعالجه هو تسجيل فوز حين يكتب المستخدم `{PlayerName} wins`.

## اكتب الاختبار أولاً

نعرف أننا نحتاج إلى صنع شيء اسمه `CLI` يتيح لنا لعب البوكر بـ`Play`. وسيحتاج إلى قراءة مدخلات المستخدم ثم تسجيل مرات الفوز في `PlayerStore`.

لكن قبل أن نقفز بعيداً إلى الأمام، لنكتب فقط اختباراً (test) يتحقق من أنه يتكامل مع `PlayerStore` كما نريد.

داخل `CLI_test.go` (في جذر المشروع، لا داخل `cmd`)

```go
// CLI_test.go
package poker

import "testing"

func TestCLI(t *testing.T) {
	playerStore := &StubPlayerStore{}
	cli := &CLI{playerStore}
	cli.PlayPoker()

	if len(playerStore.winCalls) != 1 {
		t.Fatal("expected a win call but didn't get any")
	}
}
```

- يمكننا استعمال `StubPlayerStore` من الاختبارات الأخرى
- نمرر تبعيتنا إلى النوع `CLI` غير الموجود بعد
- نبدأ اللعبة بطريقة `PlayPoker` لم تُكتب بعد
- نتحقق من أن فوزاً قد سُجّل

## حاول تشغيل الاختبار

```
# github.com/quii/learn-go-with-tests/command-line/v2
./cli_test.go:25:10: undefined: CLI
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

في هذه المرحلة، ينبغي أن تكون مرتاحاً بما يكفي لإنشاء البنية (struct) الجديدة `CLI` مع الحقل المقابل لتبعيتنا، وإضافة طريقة (method).

ينبغي أن تنتهي إلى شيفرة كهذه

```go
// CLI.go
package poker

type CLI struct {
	playerStore PlayerStore
}

func (cli *CLI) PlayPoker() {}
```

تذكّر أننا نحاول فقط جعل الاختبار يعمل كي نتحقق من أنه يفشل كما نأمل

```
--- FAIL: TestCLI (0.00s)
    cli_test.go:30: expected a win call but didn't get any
FAIL
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
//CLI.go
func (cli *CLI) PlayPoker() {
	cli.playerStore.RecordWin("Cleo")
}
```

ينبغي أن يجعله هذا ينجح.

بعد ذلك، علينا محاكاة القراءة من `Stdin` (مدخلات المستخدم) كي نستطيع تسجيل مرات فوز لاعبين محددين.

لنوسّع اختبارنا لاختبار ذلك.

## اكتب الاختبار أولاً

```go
//CLI_test.go
func TestCLI(t *testing.T) {
	in := strings.NewReader("Chris wins\n")
	playerStore := &StubPlayerStore{}

	cli := &CLI{playerStore, in}
	cli.PlayPoker()

	if len(playerStore.winCalls) != 1 {
		t.Fatal("expected a win call but didn't get any")
	}

	got := playerStore.winCalls[0]
	want := "Chris"

	if got != want {
		t.Errorf("didn't record correct winner, got %q, want %q", got, want)
	}
}
```

سنستعمل `os.Stdin` في `main` لالتقاط مدخلات المستخدم. وهو في الخفاء `*File`، مما يعني أنه يحقق `io.Reader`، الذي نعرف الآن أنه وسيلة مفيدة لالتقاط النص.

ننشئ `io.Reader` في اختبارنا باستعمال الدالة المفيدة `strings.NewReader`، ونملؤه بما نتوقع أن يكتبه المستخدم.

## حاول تشغيل الاختبار

`./CLI_test.go:12:32: too many values in struct initializer`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

علينا إضافة تبعيتنا الجديدة إلى `CLI`.

```go
//CLI.go
type CLI struct {
	playerStore PlayerStore
	in          io.Reader
}
```

```
--- FAIL: TestCLI (0.00s)
    CLI_test.go:23: didn't record the correct winner, got 'Cleo', want 'Chris'
FAIL
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

تذكّر أن تفعل الأسهل تماماً أولاً

```go
func (cli *CLI) PlayPoker() {
	cli.playerStore.RecordWin("Chris")
}
```

ينجح الاختبار. سنضيف اختباراً آخر يجبرنا على كتابة شيفرة حقيقية بعد ذلك، لكن لنُعِد الهيكلة أولاً.

## أعد الهيكلة

أجرينا سابقاً في `server_test` فحوصاً لمعرفة ما إذا كانت مرات الفوز تُسجَّل، كما نفعل هنا. لنُزِل تكرار ذلك التوكيد بنقله إلى دالة مساعدة

```go
//server_test.go
func assertPlayerWin(t testing.TB, store *StubPlayerStore, winner string) {
	t.Helper()

	if len(store.winCalls) != 1 {
		t.Fatalf("got %d calls to RecordWin want %d", len(store.winCalls), 1)
	}

	if store.winCalls[0] != winner {
		t.Errorf("did not store correct winner got %q want %q", store.winCalls[0], winner)
	}
}
```

والآن استبدل التوكيدات في `server_test.go` و`CLI_test.go` كليهما.

ينبغي أن يُقرأ الاختبار الآن هكذا

```go
//CLI_test.go
func TestCLI(t *testing.T) {
	in := strings.NewReader("Chris wins\n")
	playerStore := &StubPlayerStore{}

	cli := &CLI{playerStore, in}
	cli.PlayPoker()

	assertPlayerWin(t, playerStore, "Chris")
}
```

والآن لنكتب اختباراً _آخر_ بمدخلات مستخدم مختلفة يجبرنا على قراءتها فعلاً.

## اكتب الاختبار أولاً

```go
//CLI_test.go
func TestCLI(t *testing.T) {

	t.Run("record chris win from user input", func(t *testing.T) {
		in := strings.NewReader("Chris wins\n")
		playerStore := &StubPlayerStore{}

		cli := &CLI{playerStore, in}
		cli.PlayPoker()

		assertPlayerWin(t, playerStore, "Chris")
	})

	t.Run("record cleo win from user input", func(t *testing.T) {
		in := strings.NewReader("Cleo wins\n")
		playerStore := &StubPlayerStore{}

		cli := &CLI{playerStore, in}
		cli.PlayPoker()

		assertPlayerWin(t, playerStore, "Cleo")
	})

}
```

## حاول تشغيل الاختبار

```
=== RUN   TestCLI
--- FAIL: TestCLI (0.00s)
=== RUN   TestCLI/record_chris_win_from_user_input
    --- PASS: TestCLI/record_chris_win_from_user_input (0.00s)
=== RUN   TestCLI/record_cleo_win_from_user_input
    --- FAIL: TestCLI/record_cleo_win_from_user_input (0.00s)
        CLI_test.go:27: did not store correct winner got 'Chris' want 'Cleo'
FAIL
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

سنستعمل [`bufio.Scanner`](https://golang.org/pkg/bufio/) لقراءة المدخلات من `io.Reader`.

> تنفّذ الحزمة `bufio` إدخالاً وإخراجاً مخزّناً مؤقتاً. فهي تغلّف كائن `io.Reader` أو `io.Writer`، وتنشئ كائناً آخر (`Reader` أو `Writer`) يحقق الواجهة أيضاً، لكنه يوفر التخزين المؤقت وبعض المساعدة في الإدخال والإخراج النصي.

حدّث الشيفرة إلى ما يلي

```go
//CLI.go
type CLI struct {
	playerStore PlayerStore
	in          io.Reader
}

func (cli *CLI) PlayPoker() {
	reader := bufio.NewScanner(cli.in)
	reader.Scan()
	cli.playerStore.RecordWin(extractWinner(reader.Text()))
}

func extractWinner(userInput string) string {
	return strings.Replace(userInput, " wins", "", 1)
}
```

ستنجح الاختبارات الآن.

- ستقرأ `Scanner.Scan()` حتى السطر الجديد.
- ثم نستعمل `Scanner.Text()` لإعادة السلسلة النصية `string` التي قرأها الماسح.

والآن بعد أن صارت لدينا بعض الاختبارات الناجحة، ينبغي أن نربط هذا في `main`. وتذكّر أن علينا دائماً السعي إلى برنامج يعمل ومتكامل بالكامل بأسرع ما يمكن.

أضف ما يلي في `main.go` وشغّله. (قد تحتاج إلى تعديل مسار التبعية الثانية لتطابق ما على حاسوبك)

```go
package main

import (
	"fmt"
	"github.com/quii/learn-go-with-tests/command-line/v3"
	"log"
	"os"
)

const dbFileName = "game.db.json"

func main() {
	fmt.Println("Let's play poker")
	fmt.Println("Type {Name} wins to record a win")

	db, err := os.OpenFile(dbFileName, os.O_RDWR|os.O_CREATE, 0666)

	if err != nil {
		log.Fatalf("problem opening %s %v", dbFileName, err)
	}

	store, err := poker.NewFileSystemPlayerStore(db)

	if err != nil {
		log.Fatalf("problem creating file system player store, %v ", err)
	}

	game := poker.CLI{store, os.Stdin}
	game.PlayPoker()
}
```

ينبغي أن يظهر لك خطأ (error)

```
command-line/v3/cmd/cli/main.go:32:25: implicit assignment of unexported field 'playerStore' in poker.CLI literal
command-line/v3/cmd/cli/main.go:32:34: implicit assignment of unexported field 'in' in poker.CLI literal
```

ما يحدث هنا أننا نحاول الإسناد إلى الحقلين `playerStore` و`in` في `CLI`. وهذان حقلان غير مُصدَّرين (خاصان). كان _بإمكاننا_ فعل ذلك في شيفرة اختبارنا لأن اختبارنا في الحزمة نفسها التي فيها `CLI` (أي `poker`). لكن `main` في الحزمة `main`، لذا لا يملك الوصول إليهما.

وهذا يبرز أهمية _دمج عملك_. فقد جعلنا تبعيات `CLI` خاصة عن حق (لأننا لا نريد كشفها لمستخدمي `CLI`)، لكننا لم نوفر وسيلة للمستخدمين لبنائه.

هل هناك طريقة كنا سنكتشف بها هذه المشكلة أبكر؟

### التصريح `package mypackage_test`

في كل الأمثلة الأخرى حتى الآن، حين ننشئ ملف اختبار نصرّح عنه على أنه في الحزمة نفسها التي نختبرها.

لا بأس بهذا، وهو يعني أننا في المناسبات النادرة التي نريد فيها اختبار شيء داخلي في الحزمة نملك الوصول إلى الأنواع غير المُصدَّرة.

لكن بما أننا دعونا إلى _عدم_ اختبار الأشياء الداخلية _عموماً_، فهل تستطيع غو مساعدتنا على فرض ذلك؟ ماذا لو استطعنا اختبار شيفرتنا مع الوصول إلى الأنواع المُصدَّرة فقط (كما يفعل `main`)؟

حين تكتب مشروعاً فيه عدة حزم، أنصحك بشدة أن ينتهي اسم حزمة اختبارك بـ`_test`. فحين تفعل هذا، لن تستطيع الوصول إلا إلى الأنواع المُصدَّرة في حزمتك. وهذا سيساعد في هذه الحالة تحديداً، كما يساعد على فرض انضباط اختبار الواجهات البرمجية العامة فقط. وإن أردت مع ذلك اختبار الدواخل، فيمكنك كتابة اختبار منفصل بالحزمة التي تريد اختبارها.

من المقولات في `TDD` أنك إن لم تستطع اختبار شيفرتك، فالأرجح أن مستخدميها سيجدون صعوبة في التكامل معها. واستعمال `package foo_test` سيساعد على ذلك بإجبارك على اختبار شيفرتك كما لو كنت تستوردها كما سيفعل مستخدمو حزمتك.

قبل إصلاح `main`، لنغيّر حزمة اختبارنا داخل `CLI_test.go` إلى `poker_test`.

إن كانت لديك بيئة تطوير متكاملة مضبوطة جيداً، فسترى فجأة كثيراً من اللون الأحمر! وإن شغّلت المصرِّف (compiler) فستحصل على الأخطاء التالية

```
./CLI_test.go:12:19: undefined: StubPlayerStore
./CLI_test.go:17:3: undefined: assertPlayerWin
./CLI_test.go:22:19: undefined: StubPlayerStore
./CLI_test.go:27:3: undefined: assertPlayerWin
```

لقد صادفنا الآن مزيداً من الأسئلة حول تصميم الحزم. فلكي نختبر برنامجنا، صنعنا بدائل ثابتة ودوالاً مساعدة غير مُصدَّرة، لم تعد متاحة لنا في `CLI_test` لأن الدوال المساعدة معرّفة في ملفات `_test.go` داخل الحزمة `poker`.

#### هل نريد أن تكون بدائلنا الثابتة ودوالنا المساعدة "عامة"؟

هذا نقاش ذاتي. فقد يقول قائل إنك لا تريد تلويث الواجهة البرمجية لحزمتك بشيفرة لتسهيل الاختبارات.

في العرض التقديمي ["Advanced Testing with Go"](https://speakerdeck.com/mitchellh/advanced-testing-with-go?slide=53) لميتشل هاشيموتو، يُوصف كيف تدعو HashiCorp إلى فعل ذلك، كي يستطيع مستخدمو الحزمة كتابة الاختبارات دون إعادة اختراع العجلة بكتابة البدائل الثابتة. وفي حالتنا، يعني هذا أن أي شخص يستعمل الحزمة `poker` لن يضطر إلى إنشاء بديل ثابت خاص به لـ`PlayerStore` إن أراد العمل مع شيفرتنا.

ومن واقع تجربتي، استعملت هذا الأسلوب في حزم مشتركة أخرى، وأثبت فائدته الكبيرة في توفير وقت المستخدمين حين يتكاملون مع حزمنا.

لذا لننشئ ملفاً باسم `testing.go` ونضيف إليه بديلنا الثابت ودوالنا المساعدة.

```go
// testing.go
package poker

import "testing"

type StubPlayerStore struct {
	scores   map[string]int
	winCalls []string
	league   []Player
}

func (s *StubPlayerStore) GetPlayerScore(name string) int {
	score := s.scores[name]
	return score
}

func (s *StubPlayerStore) RecordWin(name string) {
	s.winCalls = append(s.winCalls, name)
}

func (s *StubPlayerStore) GetLeague() League {
	return s.league
}

func AssertPlayerWin(t testing.TB, store *StubPlayerStore, winner string) {
	t.Helper()

	if len(store.winCalls) != 1 {
		t.Fatalf("got %d calls to RecordWin want %d", len(store.winCalls), 1)
	}

	if store.winCalls[0] != winner {
		t.Errorf("did not store correct winner got %q want %q", store.winCalls[0], winner)
	}
}

// todo for you - the rest of the helpers
```

ستحتاج إلى جعل الدوال المساعدة عامة (تذكّر أن التصدير يكون بحرف كبير في البداية) إن أردت كشفها لمن يستوردون حزمتنا.

وفي اختبار `CLI` ستحتاج إلى استدعاء الشيفرة كما لو كنت تستعملها من حزمة مختلفة.

```go
//CLI_test.go
func TestCLI(t *testing.T) {

	t.Run("record chris win from user input", func(t *testing.T) {
		in := strings.NewReader("Chris wins\n")
		playerStore := &poker.StubPlayerStore{}

		cli := &poker.CLI{playerStore, in}
		cli.PlayPoker()

		poker.AssertPlayerWin(t, playerStore, "Chris")
	})

	t.Run("record cleo win from user input", func(t *testing.T) {
		in := strings.NewReader("Cleo wins\n")
		playerStore := &poker.StubPlayerStore{}

		cli := &poker.CLI{playerStore, in}
		cli.PlayPoker()

		poker.AssertPlayerWin(t, playerStore, "Cleo")
	})

}
```

سترى الآن أن لدينا المشكلات نفسها التي كانت في `main`

```
./CLI_test.go:15:26: implicit assignment of unexported field 'playerStore' in poker.CLI literal
./CLI_test.go:15:39: implicit assignment of unexported field 'in' in poker.CLI literal
./CLI_test.go:25:26: implicit assignment of unexported field 'playerStore' in poker.CLI literal
./CLI_test.go:25:39: implicit assignment of unexported field 'in' in poker.CLI literal
```

أسهل طريقة لتجاوز ذلك هي صنع دالة بانية كما فعلنا مع الأنواع الأخرى. وسنغيّر أيضاً `CLI` بحيث يخزّن `bufio.Scanner` بدلاً من القارئ، لأنه صار يُغلَّف تلقائياً وقت البناء.

```go
//CLI.go
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
```

وبهذا يمكننا بعد ذلك تبسيط شيفرة القراءة وإعادة هيكلتها

```go
//CLI.go
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

غيّر الاختبار ليستعمل الدالة البانية بدلاً من ذلك، وينبغي أن نعود إلى اختبارات ناجحة.

وأخيراً، يمكننا العودة إلى `main.go` الجديد واستعمال الدالة البانية التي صنعناها للتو

```go
//cmd/cli/main.go
game := poker.NewCLI(store, os.Stdin)
```

حاول تشغيله، واكتب "Bob wins".

### أعد الهيكلة

لدينا شيء من التكرار في تطبيقينا، حيث نفتح ملفاً وننشئ `file_system_store` من محتوياته. ويبدو هذا ضعفاً طفيفاً في تصميم حزمتنا، لذا ينبغي أن ننشئ فيها دالة (function) تغلّف فتح ملف من مسار وإعادة `PlayerStore`.

```go
//file_system_store.go
func FileSystemPlayerStoreFromFile(path string) (*FileSystemPlayerStore, func(), error) {
	db, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE, 0666)

	if err != nil {
		return nil, nil, fmt.Errorf("problem opening %s %v", path, err)
	}

	closeFunc := func() {
		db.Close()
	}

	store, err := NewFileSystemPlayerStore(db)

	if err != nil {
		return nil, nil, fmt.Errorf("problem creating file system player store, %v ", err)
	}

	return store, closeFunc, nil
}
```

والآن أعد هيكلة التطبيقين كليهما لاستعمال هذه الدالة لإنشاء المخزن.

#### شيفرة تطبيق سطر الأوامر

```go
// cmd/cli/main.go
package main

import (
	"fmt"
	"github.com/quii/learn-go-with-tests/command-line/v3"
	"log"
	"os"
)

const dbFileName = "game.db.json"

func main() {
	store, close, err := poker.FileSystemPlayerStoreFromFile(dbFileName)

	if err != nil {
		log.Fatal(err)
	}
	defer close()

	fmt.Println("Let's play poker")
	fmt.Println("Type {Name} wins to record a win")
	poker.NewCLI(store, os.Stdin).PlayPoker()
}
```

#### شيفرة تطبيق خادم الويب

```go
// cmd/webserver/main.go
package main

import (
	"github.com/quii/learn-go-with-tests/command-line/v3"
	"log"
	"net/http"
)

const dbFileName = "game.db.json"

func main() {
	store, close, err := poker.FileSystemPlayerStoreFromFile(dbFileName)

	if err != nil {
		log.Fatal(err)
	}
	defer close()

	server := poker.NewPlayerServer(store)

	if err := http.ListenAndServe(":5000", server); err != nil {
		log.Fatalf("could not listen on port 5000 %v", err)
	}
}
```

لاحظ التناظر: رغم أنهما واجهتا مستخدم مختلفتان، فإن الإعداد يكاد يكون متطابقاً. ويبدو هذا تحققاً جيداً من تصميمنا حتى الآن.
ولاحظ أيضاً أن `FileSystemPlayerStoreFromFile` تعيد دالة إغلاق، كي نستطيع إغلاق الملف الأساسي بمجرد أن ننتهي من استعمال المخزن.

## الخلاصة

### بنية الحزم

أردنا في هذا الفصل إنشاء تطبيقين، مع إعادة استعمال شيفرة المجال التي كتبناها حتى الآن. ولفعل ذلك، احتجنا إلى تحديث بنية حزمنا بحيث تكون لدينا مجلدات منفصلة لكل `main`.

وبفعل ذلك واجهنا مشكلات تكامل بسبب القيم غير المُصدَّرة، وهذا يبيّن أكثر قيمة العمل على "شرائح" صغيرة والدمج كثيراً.

وتعلّمنا كيف يساعدنا `mypackage_test` على إنشاء بيئة اختبار تقدّم التجربة نفسها التي تمر بها الحزم الأخرى حين تتكامل مع شيفرتك، لتساعدك على اكتشاف مشكلات التكامل ورؤية مدى سهولة (أو صعوبة!) العمل مع شيفرتك.

### قراءة مدخلات المستخدم

رأينا كيف أن القراءة من `os.Stdin` سهلة جداً بالنسبة إلينا لأنه يحقق `io.Reader`. واستعملنا `bufio.Scanner` لقراءة مدخلات المستخدم سطراً سطراً بسهولة.

### التجريدات البسيطة تقود إلى إعادة استعمال أبسط للشيفرة

لم يتطلب دمج `PlayerStore` في تطبيقنا الجديد أي جهد تقريباً (بعد أن أجرينا تعديلات الحزم)، وبالتالي كان الاختبار سهلاً جداً أيضاً، لأننا قررنا كشف نسختنا الثابتة البديلة أيضاً.
