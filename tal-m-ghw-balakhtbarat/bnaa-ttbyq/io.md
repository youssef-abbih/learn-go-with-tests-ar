# الإدخال والإخراج والترتيب

**[تجد كل شيفرة هذا الفصل هنا](https://github.com/quii/learn-go-with-tests/tree/main/io)**

[في الفصل السابق](json.md) واصلنا التقدم في تطبيقنا بإضافة نقطة نهاية جديدة `/league`. وتعلّمنا في الطريق كيف نتعامل مع JSON، وتضمين الأنواع، والتوجيه.

مالكة المنتج منزعجة بعض الشيء من أن البرنامج يفقد النتائج حين يُعاد تشغيل الخادم. وذلك لأن تنفيذنا للمخزن في الذاكرة. وهي أيضاً غير راضية لأننا لم نفهم أن نقطة النهاية `/league` ينبغي أن تعيد اللاعبين مرتبين بحسب عدد مرات الفوز!

## الشيفرة حتى الآن

```go
// server.go
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

// PlayerStore stores score information about players
type PlayerStore interface {
	GetPlayerScore(name string) int
	RecordWin(name string)
	GetLeague() []Player
}

// Player stores a name with a number of wins
type Player struct {
	Name string
	Wins int
}

// PlayerServer is a HTTP interface for player information
type PlayerServer struct {
	store PlayerStore
	http.Handler
}

const jsonContentType = "application/json"

// NewPlayerServer creates a PlayerServer with routing configured
func NewPlayerServer(store PlayerStore) *PlayerServer {
	p := new(PlayerServer)

	p.store = store

	router := http.NewServeMux()
	router.Handle("/league", http.HandlerFunc(p.leagueHandler))
	router.Handle("/players/", http.HandlerFunc(p.playersHandler))

	p.Handler = router

	return p
}

func (p *PlayerServer) leagueHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("content-type", jsonContentType)
	json.NewEncoder(w).Encode(p.store.GetLeague())
}

func (p *PlayerServer) playersHandler(w http.ResponseWriter, r *http.Request) {
	player := strings.TrimPrefix(r.URL.Path, "/players/")

	switch r.Method {
	case http.MethodPost:
		p.processWin(w, player)
	case http.MethodGet:
		p.showScore(w, player)
	}
}

func (p *PlayerServer) showScore(w http.ResponseWriter, player string) {
	score := p.store.GetPlayerScore(player)

	if score == 0 {
		w.WriteHeader(http.StatusNotFound)
	}

	fmt.Fprint(w, score)
}

func (p *PlayerServer) processWin(w http.ResponseWriter, player string) {
	p.store.RecordWin(player)
	w.WriteHeader(http.StatusAccepted)
}
```

```go
// in_memory_player_store.go
package main

func NewInMemoryPlayerStore() *InMemoryPlayerStore {
	return &InMemoryPlayerStore{map[string]int{}}
}

type InMemoryPlayerStore struct {
	store map[string]int
}

func (i *InMemoryPlayerStore) GetLeague() []Player {
	var league []Player
	for name, wins := range i.store {
		league = append(league, Player{name, wins})
	}
	return league
}

func (i *InMemoryPlayerStore) RecordWin(name string) {
	i.store[name]++
}

func (i *InMemoryPlayerStore) GetPlayerScore(name string) int {
	return i.store[name]
}
```

```go
// main.go
package main

import (
	"log"
	"net/http"
)

func main() {
	server := NewPlayerServer(NewInMemoryPlayerStore())
	log.Fatal(http.ListenAndServe(":5000", server))
}
```

يمكنك إيجاد الاختبارات المقابلة في الرابط أعلى الفصل.

## خزّن البيانات

هناك عشرات قواعد البيانات التي يمكننا استعمالها لهذا، لكننا سنختار أسلوباً بسيطاً جداً. سنخزّن بيانات هذا التطبيق بصيغة JSON في ملف.

وهذا يُبقي البيانات سهلة النقل جداً، وتنفيذه بسيط نسبياً.

لن يتوسع جيداً على نحو خاص، لكن بما أن هذا نموذج أولي فسيكون مقبولاً في الوقت الحالي. وإن تغيرت ظروفنا ولم يعد مناسباً، فسيكون من السهل استبداله بشيء مختلف بفضل التجريد `PlayerStore` الذي استعملناه.

سنُبقي `InMemoryPlayerStore` في الوقت الحالي كي تظل اختبارات التكامل ناجحة ريثما نطوّر مخزننا الجديد. وبمجرد أن نثق بأن تنفيذنا الجديد كافٍ لجعل اختبار التكامل ينجح، سنستبدله به ثم نحذف `InMemoryPlayerStore`.

## اكتب الاختبار أولاً

ينبغي أن تكون الآن مألوفاً مع واجهات المكتبة القياسية لقراءة البيانات (`io.Reader`) وكتابتها (`io.Writer`)، ومع كيفية استعمال المكتبة القياسية لاختبار هذه الدوال دون الحاجة إلى استعمال ملفات حقيقية.

لكي يكتمل هذا العمل سنحتاج إلى تنفيذ `PlayerStore`، لذا سنكتب اختبارات لمخزننا تستدعي الطرق (methods) التي علينا تنفيذها. وسنبدأ بـ`GetLeague`.

```go
//file_system_store_test.go
func TestFileSystemStore(t *testing.T) {

	t.Run("league from a reader", func(t *testing.T) {
		database := strings.NewReader(`[
			{"Name": "Cleo", "Wins": 10},
			{"Name": "Chris", "Wins": 33}]`)

		store := FileSystemPlayerStore{database}

		got := store.GetLeague()

		want := []Player{
			{"Cleo", 10},
			{"Chris", 33},
		}

		assertLeague(t, got, want)
	})
}
```

نستعمل `strings.NewReader` التي ستعيد لنا `Reader`، وهو ما سيستعمله `FileSystemPlayerStore` لقراءة البيانات. وفي `main` سنفتح ملفاً، وهو أيضاً `Reader`.

## حاول تشغيل الاختبار

```
# github.com/quii/learn-go-with-tests/io/v1
./file_system_store_test.go:15:12: undefined: FileSystemPlayerStore
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

لنعرّف `FileSystemPlayerStore` في ملف جديد

```go
//file_system_store.go
type FileSystemPlayerStore struct{}
```

حاول مجدداً

```
# github.com/quii/learn-go-with-tests/io/v1
./file_system_store_test.go:15:28: too many values in struct initializer
./file_system_store_test.go:17:15: store.GetLeague undefined (type FileSystemPlayerStore has no field or method GetLeague)
```

يعترض لأننا نمرر `Reader` لكنه لا يتوقع واحداً، ولأنه لم تُعرَّف فيه `GetLeague` بعد.

```go
//file_system_store.go
type FileSystemPlayerStore struct {
	database io.Reader
}

func (f *FileSystemPlayerStore) GetLeague() []Player {
	return nil
}
```

محاولة أخرى...

```
=== RUN   TestFileSystemStore//league_from_a_reader
    --- FAIL: TestFileSystemStore//league_from_a_reader (0.00s)
        file_system_store_test.go:24: got [] want [{Cleo 10} {Chris 33}]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

قرأنا JSON من قارئ من قبل

```go
//file_system_store.go
func (f *FileSystemPlayerStore) GetLeague() []Player {
	var league []Player
	json.NewDecoder(f.database).Decode(&league)
	return league
}
```

ينبغي أن ينجح الاختبار (test).

## أعد الهيكلة

لقد فعلنا هذا من قبل _بالفعل_! فقد اضطرت شيفرة اختبار الخادم إلى فك ترميز JSON من الاستجابة.

لنحاول إزالة التكرار بنقل ذلك إلى دالة (function).

أنشئ ملفاً جديداً باسم `league.go` وضع فيه ما يلي.

```go
//league.go
func NewLeague(rdr io.Reader) ([]Player, error) {
	var league []Player
	err := json.NewDecoder(rdr).Decode(&league)
	if err != nil {
		err = fmt.Errorf("problem parsing league, %v", err)
	}

	return league, err
}
```

استدعِ هذه الدالة في تنفيذنا، وفي الدالة المساعدة للاختبار `getLeagueFromResponse` في `server_test.go`

```go
//file_system_store.go
func (f *FileSystemPlayerStore) GetLeague() []Player {
	league, _ := NewLeague(f.database)
	return league
}
```

ليست لدينا بعد استراتيجية للتعامل مع أخطاء التحليل، لكن لنواصل.

### مشكلات التنقل في الملف

في تنفيذنا خلل. أولاً، لنذكّر أنفسنا بكيفية تعريف `io.Reader`.

```go
type Reader interface {
	Read(p []byte) (n int, err error)
}
```

مع ملفنا، يمكنك أن تتخيله يقرأ بايتاً بايتاً حتى النهاية. فماذا يحدث إن حاولت القراءة بـ`Read` مرة ثانية؟

أضف ما يلي إلى نهاية اختبارنا الحالي.

```go
//file_system_store_test.go

// read again
got = store.GetLeague()
assertLeague(t, got, want)
```

نريد أن ينجح هذا، لكنه لا ينجح إن شغّلت الاختبار.

المشكلة أن `Reader` قد وصل إلى النهاية، فلا يبقى شيء للقراءة. ونحتاج إلى وسيلة لنطلب منه العودة إلى البداية.

الواجهة [ReadSeeker](https://golang.org/pkg/io/#ReadSeeker) واجهة أخرى في المكتبة القياسية يمكن أن تساعد.

```go
type ReadSeeker interface {
	Reader
	Seeker
}
```

هل تذكر التضمين؟ هذه واجهة (interface) مركّبة من `Reader` و[`Seeker`](https://golang.org/pkg/io/#Seeker)

```go
type Seeker interface {
	Seek(offset int64, whence int) (int64, error)
}
```

يبدو هذا جيداً، فهل يمكننا تغيير `FileSystemPlayerStore` ليأخذ هذه الواجهة بدلاً من ذلك؟

```go
//file_system_store.go
type FileSystemPlayerStore struct {
	database io.ReadSeeker
}

func (f *FileSystemPlayerStore) GetLeague() []Player {
	f.database.Seek(0, io.SeekStart)
	league, _ := NewLeague(f.database)
	return league
}
```

حاول تشغيل الاختبار، فهو ينجح الآن! ولحسن حظنا، `strings.NewReader` التي استعملناها في اختبارنا تحقق أيضاً `ReadSeeker`، لذا لم نضطر إلى إجراء أي تغييرات أخرى.

بعد ذلك سننفّذ `GetPlayerScore`.

## اكتب الاختبار أولاً

```go
//file_system_store_test.go
t.Run("get player score", func(t *testing.T) {
	database := strings.NewReader(`[
		{"Name": "Cleo", "Wins": 10},
		{"Name": "Chris", "Wins": 33}]`)

	store := FileSystemPlayerStore{database}

	got := store.GetPlayerScore("Chris")

	want := 33

	if got != want {
		t.Errorf("got %d want %d", got, want)
	}
})
```

## حاول تشغيل الاختبار

```
./file_system_store_test.go:38:15: store.GetPlayerScore undefined (type FileSystemPlayerStore has no field or method GetPlayerScore)
```

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

علينا إضافة الطريقة إلى نوعنا الجديد كي يُصرَّف الاختبار.

```go
//file_system_store.go
func (f *FileSystemPlayerStore) GetPlayerScore(name string) int {
	return 0
}
```

صار يُصرَّف الآن والاختبار يفشل

```
=== RUN   TestFileSystemStore/get_player_score
    --- FAIL: TestFileSystemStore//get_player_score (0.00s)
        file_system_store_test.go:43: got 0 want 33
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

يمكننا المرور على الدوري لإيجاد اللاعب وإعادة نتيجته

```go
//file_system_store.go
func (f *FileSystemPlayerStore) GetPlayerScore(name string) int {

	var wins int

	for _, player := range f.GetLeague() {
		if player.Name == name {
			wins = player.Wins
			break
		}
	}

	return wins
}
```

## أعد الهيكلة

لقد رأيت عشرات عمليات إعادة هيكلة الدوال المساعدة للاختبار، لذا سأترك لك جعل هذا يعمل

```go
//file_system_store_test.go
t.Run("get player score", func(t *testing.T) {
	database := strings.NewReader(`[
		{"Name": "Cleo", "Wins": 10},
		{"Name": "Chris", "Wins": 33}]`)

	store := FileSystemPlayerStore{database}

	got := store.GetPlayerScore("Chris")
	want := 33
	assertScoreEquals(t, got, want)
})
```

وأخيراً، علينا البدء بتسجيل النتائج بـ`RecordWin`.

## اكتب الاختبار أولاً

أسلوبنا قصير النظر إلى حد ما في الكتابة. فلا نستطيع (بسهولة) تحديث "صف" واحد من JSON في ملف. بل سنحتاج إلى تخزين التمثيل الجديد _كاملاً_ لقاعدة بياناتنا مع كل كتابة.

كيف نكتب؟ عادةً نستعمل `Writer`، لكن لدينا بالفعل `ReadSeeker`. يمكننا أن نجعل لدينا تبعيتين، لكن في المكتبة القياسية بالفعل واجهة لنا هي `ReadWriteSeeker`، تتيح لنا فعل كل ما سنحتاج إليه مع ملف.

لنحدّث نوعنا

```go
//file_system_store.go
type FileSystemPlayerStore struct {
	database io.ReadWriteSeeker
}
```

لنرَ إن كان يُصرَّف

```
./file_system_store_test.go:15:34: cannot use database (type *strings.Reader) as type io.ReadWriteSeeker in field value:
    *strings.Reader does not implement io.ReadWriteSeeker (missing Write method)
./file_system_store_test.go:36:34: cannot use database (type *strings.Reader) as type io.ReadWriteSeeker in field value:
    *strings.Reader does not implement io.ReadWriteSeeker (missing Write method)
```

ليس مفاجئاً كثيراً أن `strings.Reader` لا يحقق `ReadWriteSeeker`، فماذا نفعل؟

أمامنا خياران

- إنشاء ملف مؤقت لكل اختبار. فالنوع `*os.File` يحقق `ReadWriteSeeker`. وميزة هذا أنه يصبح أقرب إلى اختبار تكامل، فنحن نقرأ ونكتب فعلاً من نظام الملفات، وهذا سيمنحنا مستوى عالياً جداً من الثقة. أما عيوبه فهي أننا نفضّل اختبارات الوحدة لأنها أسرع وأبسط عموماً. كما سنحتاج إلى مزيد من العمل حول إنشاء الملفات المؤقتة ثم التأكد من حذفها بعد الاختبار.
- يمكننا استعمال مكتبة طرف ثالث. فقد كتب [Mattetti](https://github.com/mattetti) مكتبة [filebuffer](https://github.com/mattetti/filebuffer) تحقق الواجهة التي نحتاج إليها ولا تلمس نظام الملفات.

لا أظن أن هناك إجابة خاطئة بشكل خاص هنا، لكن باختيار استعمال مكتبة طرف ثالث سأضطر إلى شرح إدارة التبعيات! لذا سنستعمل الملفات بدلاً من ذلك.

قبل إضافة اختبارنا، علينا جعل اختباراتنا الأخرى تُصرَّف باستبدال `strings.Reader` بـ`os.File`.

لننشئ بعض الدوال المساعدة التي تنشئ ملفاً مؤقتاً فيه بعض البيانات، ونجرّد اختبارات النتائج

```go
//file_system_store_test.go
func createTempFile(t testing.TB, initialData string) (io.ReadWriteSeeker, func()) {
	t.Helper()

	tmpfile, err := os.CreateTemp("", "db")

	if err != nil {
		t.Fatalf("could not create temp file %v", err)
	}

	tmpfile.Write([]byte(initialData))

	removeFile := func() {
		tmpfile.Close()
		os.Remove(tmpfile.Name())
	}

	return tmpfile, removeFile
}

func assertScoreEquals(t testing.TB, got, want int) {
	t.Helper()
	if got != want {
		t.Errorf("got %d want %d", got, want)
	}
}
```

تنشئ [CreateTemp](https://pkg.go.dev/os#CreateTemp) ملفاً مؤقتاً لنستعمله. والقيمة `"db"` التي مررناها بادئة تُوضع على اسم ملف عشوائي ستنشئه. وهذا لضمان ألا يتعارض مع ملفات أخرى عن طريق الخطأ.

ستلاحظ أننا لا نعيد `ReadWriteSeeker` (الملف) فقط، بل دالة أيضاً. فعلينا التأكد من حذف الملف بمجرد انتهاء الاختبار. ولا نريد تسريب تفاصيل الملفات إلى الاختبار، لأن ذلك عرضة للأخطاء وغير مثير لاهتمام القارئ. وبإعادة الدالة `removeFile` يمكننا الاعتناء بالتفاصيل في دالتنا المساعدة، وكل ما على المستدعي فعله هو تنفيذ `defer removeFile()`.

```go
//file_system_store_test.go
func TestFileSystemStore(t *testing.T) {

	t.Run("league from a reader", func(t *testing.T) {
		database, removeFile := createTempFile(t, `[
			{"Name": "Cleo", "Wins": 10},
			{"Name": "Chris", "Wins": 33}]`)
		defer removeFile()

		store := FileSystemPlayerStore{database}

		got := store.GetLeague()

		want := []Player{
			{"Cleo", 10},
			{"Chris", 33},
		}

		assertLeague(t, got, want)

		// read again
		got = store.GetLeague()
		assertLeague(t, got, want)
	})

	t.Run("get player score", func(t *testing.T) {
		database, removeFile := createTempFile(t, `[
			{"Name": "Cleo", "Wins": 10},
			{"Name": "Chris", "Wins": 33}]`)
		defer removeFile()

		store := FileSystemPlayerStore{database}

		got := store.GetPlayerScore("Chris")
		want := 33
		assertScoreEquals(t, got, want)
	})
}
```

شغّل الاختبارات، وينبغي أن تنجح! كانت هناك تغييرات لا بأس بها، لكن يبدو الآن أن تعريف واجهتنا قد اكتمل، وينبغي أن تكون إضافة اختبارات جديدة سهلة جداً من الآن فصاعداً.

لننجز التكرار الأول لتسجيل فوز للاعب موجود

```go
//file_system_store_test.go
t.Run("store wins for existing players", func(t *testing.T) {
	database, removeFile := createTempFile(t, `[
		{"Name": "Cleo", "Wins": 10},
		{"Name": "Chris", "Wins": 33}]`)
	defer removeFile()

	store := FileSystemPlayerStore{database}

	store.RecordWin("Chris")

	got := store.GetPlayerScore("Chris")
	want := 34
	assertScoreEquals(t, got, want)
})
```

## حاول تشغيل الاختبار

`./file_system_store_test.go:67:8: store.RecordWin undefined (type FileSystemPlayerStore has no field or method RecordWin)`

## اكتب أقل قدر من الشيفرة لتشغيل الاختبار وتحقق من مخرجات الاختبار الفاشل

أضف الطريقة الجديدة

```go
//file_system_store.go
func (f *FileSystemPlayerStore) RecordWin(name string) {

}
```

```
=== RUN   TestFileSystemStore/store_wins_for_existing_players
    --- FAIL: TestFileSystemStore/store_wins_for_existing_players (0.00s)
        file_system_store_test.go:71: got 33 want 34
```

تنفيذنا فارغ، لذا تُعاد النتيجة القديمة.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
//file_system_store.go
func (f *FileSystemPlayerStore) RecordWin(name string) {
	league := f.GetLeague()

	for i, player := range league {
		if player.Name == name {
			league[i].Wins++
		}
	}

	f.database.Seek(0, io.SeekStart)
	json.NewEncoder(f.database).Encode(league)
}
```

لعلك تسأل نفسك لماذا أكتب `league[i].Wins++` بدلاً من `player.Wins++`.

حين تمر بـ`range` على شريحة (slice)، يُعاد إليك الفهرس الحالي للحلقة (في حالتنا `i`) و_نسخة_ من العنصر عند ذلك الفهرس. وتغيير قيمة `Wins` في النسخة لن يكون له أي أثر على الشريحة `league` التي نمر عليها. لهذا السبب، علينا الحصول على المرجع إلى القيمة الفعلية بكتابة `league[i]` ثم تغيير تلك القيمة بدلاً من ذلك.

إن شغّلت الاختبارات، فينبغي أن تنجح الآن.

## أعد الهيكلة

في `GetPlayerScore` و`RecordWin` نمر على `[]Player` لإيجاد لاعب بالاسم.

يمكننا إعادة هيكلة هذه الشيفرة المشتركة داخل `FileSystemStore`، لكنها تبدو لي شيفرة مفيدة ربما يمكننا رفعها إلى نوع (type) جديد. فالعمل مع "الدوري" كان دائماً حتى الآن باستعمال `[]Player`، لكن يمكننا إنشاء نوع جديد باسم `League`. وهذا سيكون أسهل فهماً للمطورين الآخرين، ثم يمكننا إرفاق طرق مفيدة بذلك النوع لنستعملها.

أضف ما يلي داخل `league.go`

```go
//league.go
type League []Player

func (l League) Find(name string) *Player {
	for i, p := range l {
		if p.Name == name {
			return &l[i]
		}
	}
	return nil
}
```

والآن إن كان لدى أي أحد `League`، فيمكنه بسهولة إيجاد لاعب معيّن.

غيّر الواجهة `PlayerStore` لتعيد `League` بدلاً من `[]Player`. وحاول إعادة تشغيل الاختبارات، فستحصل على مشكلة تصريف لأننا غيّرنا الواجهة، لكن إصلاحها سهل جداً؛ غيّر فقط نوع القيمة المعادة من `[]Player` إلى `League`.

وهذا يتيح لنا تبسيط طرقنا في `file_system_store`.

```go
//file_system_store.go
func (f *FileSystemPlayerStore) GetPlayerScore(name string) int {

	player := f.GetLeague().Find(name)

	if player != nil {
		return player.Wins
	}

	return 0
}

func (f *FileSystemPlayerStore) RecordWin(name string) {
	league := f.GetLeague()
	player := league.Find(name)

	if player != nil {
		player.Wins++
	}

	f.database.Seek(0, io.SeekStart)
	json.NewEncoder(f.database).Encode(league)
}
```

يبدو هذا أفضل بكثير، ويمكننا أن نرى كيف قد نجد وظائف مفيدة أخرى حول `League` يمكن إعادة هيكلتها.

علينا الآن معالجة سيناريو تسجيل مرات فوز لاعبين جدد.

## اكتب الاختبار أولاً

```go
//file_system_store_test.go
t.Run("store wins for new players", func(t *testing.T) {
	database, removeFile := createTempFile(t, `[
		{"Name": "Cleo", "Wins": 10},
		{"Name": "Chris", "Wins": 33}]`)
	defer removeFile()

	store := FileSystemPlayerStore{database}

	store.RecordWin("Pepper")

	got := store.GetPlayerScore("Pepper")
	want := 1
	assertScoreEquals(t, got, want)
})
```

## حاول تشغيل الاختبار

```
=== RUN   TestFileSystemStore/store_wins_for_new_players#01
    --- FAIL: TestFileSystemStore/store_wins_for_new_players#01 (0.00s)
        file_system_store_test.go:86: got 0 want 1
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

علينا فقط معالجة السيناريو الذي تعيد فيه `Find` القيمة `nil` لأنها لم تجد اللاعب.

```go
//file_system_store.go
func (f *FileSystemPlayerStore) RecordWin(name string) {
	league := f.GetLeague()
	player := league.Find(name)

	if player != nil {
		player.Wins++
	} else {
		league = append(league, Player{name, 1})
	}

	f.database.Seek(0, io.SeekStart)
	json.NewEncoder(f.database).Encode(league)
}
```

يبدو المسار الناجح جيداً، لذا يمكننا الآن تجربة استعمال `Store` الجديد في اختبار التكامل. وهذا سيمنحنا ثقة أكبر بأن البرنامج يعمل، ثم يمكننا حذف `InMemoryPlayerStore` الزائد عن الحاجة.

استبدل المخزن القديم في `TestRecordingWinsAndRetrievingThem`.

```go
//server_integration_test.go
database, removeFile := createTempFile(t, "")
defer removeFile()
store := &FileSystemPlayerStore{database}
```

إن شغّلت الاختبار فينبغي أن ينجح، ويمكننا الآن حذف `InMemoryPlayerStore`. وستظهر الآن مشكلات تصريف في `main.go`، وهذا سيدفعنا إلى استعمال مخزننا الجديد في الشيفرة "الحقيقية".

```go
// main.go
package main

import (
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

	store := &FileSystemPlayerStore{db}
	server := NewPlayerServer(store)

	if err := http.ListenAndServe(":5000", server); err != nil {
		log.Fatalf("could not listen on port 5000 %v", err)
	}
}
```

- ننشئ ملفاً لقاعدة بياناتنا.
- الوسيط الثاني لـ`os.OpenFile` يتيح لك تحديد أذونات فتح الملف، وفي حالتنا `O_RDWR` تعني أننا نريد القراءة والكتابة، _و_`os.O_CREATE` تعني إنشاء الملف إن لم يكن موجوداً.
- الوسيط الثالث يضبط أذونات الملف، وفي حالتنا يستطيع كل المستخدمين قراءة الملف والكتابة فيه. [(انظر superuser.com لشرح أكثر تفصيلاً)](https://superuser.com/questions/295591/what-is-the-meaning-of-chmod-666).

صار تشغيل البرنامج الآن يحفظ البيانات في ملف بين عمليات إعادة التشغيل، رائع!

## مزيد من إعادة الهيكلة واهتمامات الأداء

في كل مرة يستدعي فيها أحدهم `GetLeague()` أو `GetPlayerScore()` نقرأ الملف كله ونحلله من JSON. ولا ينبغي أن نضطر إلى ذلك، لأن `FileSystemStore` مسؤول بالكامل عن حالة الدوري؛ فلا ينبغي أن يحتاج إلى قراءة الملف إلا حين يبدأ البرنامج، ولا إلى تحديثه إلا حين تتغير البيانات.

يمكننا إنشاء دالة بانية تجري لنا بعض هذه التهيئة، وتخزّن الدوري كقيمة في `FileSystemStore` لتُستعمل في عمليات القراءة بدلاً من ذلك.

```go
//file_system_store.go
type FileSystemPlayerStore struct {
	database io.ReadWriteSeeker
	league   League
}

func NewFileSystemPlayerStore(database io.ReadWriteSeeker) *FileSystemPlayerStore {
	database.Seek(0, io.SeekStart)
	league, _ := NewLeague(database)
	return &FileSystemPlayerStore{
		database: database,
		league:   league,
	}
}
```

بهذه الطريقة لا نضطر إلى القراءة من القرص إلا مرة واحدة. ويمكننا الآن استبدال كل استدعاءاتنا السابقة لجلب الدوري من القرص، واستعمال `f.league` بدلاً منها.

```go
//file_system_store.go
func (f *FileSystemPlayerStore) GetLeague() League {
	return f.league
}

func (f *FileSystemPlayerStore) GetPlayerScore(name string) int {

	player := f.league.Find(name)

	if player != nil {
		return player.Wins
	}

	return 0
}

func (f *FileSystemPlayerStore) RecordWin(name string) {
	player := f.league.Find(name)

	if player != nil {
		player.Wins++
	} else {
		f.league = append(f.league, Player{name, 1})
	}

	f.database.Seek(0, io.SeekStart)
	json.NewEncoder(f.database).Encode(f.league)
}
```

إن حاولت تشغيل الاختبارات فستعترض الآن على تهيئة `FileSystemPlayerStore`، فأصلحها فقط باستدعاء الدالة البانية الجديدة.

### مشكلة أخرى

هناك سذاجة أخرى في طريقة تعاملنا مع الملفات _قد_ تُحدث خطأً برمجياً سيئاً جداً لاحقاً.

حين ننفّذ `RecordWin` نعود بـ`Seek` إلى بداية الملف ثم نكتب البيانات الجديدة، لكن ماذا لو كانت البيانات الجديدة أصغر مما كان موجوداً من قبل؟

في حالتنا الحالية، هذا مستحيل. فنحن لا نعدّل النتائج ولا نحذفها أبداً، لذا لا يمكن للبيانات إلا أن تكبر. لكن من غير المسؤول أن نترك الشيفرة هكذا؛ فليس من المستبعد أن يظهر سيناريو حذف.

لكن كيف سنختبر هذا؟ ما علينا فعله أولاً هو إعادة هيكلة شيفرتنا بحيث نفصل اهتمام _نوع البيانات التي نكتبها عن عملية الكتابة نفسها_. ثم يمكننا اختبار ذلك منفصلاً للتحقق من أنه يعمل كما نأمل.

سننشئ نوعاً جديداً لتغليف وظيفة "حين نكتب نبدأ من البداية". وسأسميه `Tape`. أنشئ ملفاً جديداً بما يلي:

```go
// tape.go
package main

import "io"

type tape struct {
	file io.ReadWriteSeeker
}

func (t *tape) Write(p []byte) (n int, err error) {
	t.file.Seek(0, io.SeekStart)
	return t.file.Write(p)
}
```

لاحظ أننا لا ننفّذ الآن إلا `Write`، لأنها تغلّف جزء `Seek`. وهذا يعني أن `FileSystemStore` يمكن أن يحتفظ بمرجع إلى `Writer` بدلاً من ذلك.

```go
//file_system_store.go
type FileSystemPlayerStore struct {
	database io.Writer
	league   League
}
```

حدّث الدالة البانية لتستعمل `Tape`

```go
//file_system_store.go
func NewFileSystemPlayerStore(database io.ReadWriteSeeker) *FileSystemPlayerStore {
	database.Seek(0, io.SeekStart)
	league, _ := NewLeague(database)

	return &FileSystemPlayerStore{
		database: &tape{database},
		league:   league,
	}
}
```

وأخيراً، يمكننا الحصول على المكسب المذهل الذي أردناه بحذف استدعاء `Seek` من `RecordWin`. نعم، لا يبدو الأمر كبيراً، لكنه على الأقل يعني أننا إن أجرينا أي نوع آخر من الكتابة، يمكننا الاعتماد على `Write` لتتصرف كما نحتاج إليها. وفوق ذلك، سيتيح لنا الآن اختبار الشيفرة التي قد تكون إشكالية بشكل منفصل وإصلاحها.

لنكتب الاختبار الذي نريد فيه تحديث المحتويات الكاملة لملف بشيء أصغر من المحتويات الأصلية.

## اكتب الاختبار أولاً

سينشئ اختبارنا ملفاً فيه بعض المحتوى، ويحاول الكتابة فيه باستعمال `tape`، ثم يقرأ كل شيء مجدداً ليرى ما في الملف. في `tape_test.go`:

```go
//tape_test.go
func TestTape_Write(t *testing.T) {
	file, clean := createTempFile(t, "12345")
	defer clean()

	tape := &tape{file}

	tape.Write([]byte("abc"))

	file.Seek(0, io.SeekStart)
	newFileContents, _ := io.ReadAll(file)

	got := string(newFileContents)
	want := "abc"

	if got != want {
		t.Errorf("got %q want %q", got, want)
	}
}
```

## حاول تشغيل الاختبار

```
=== RUN   TestTape_Write
--- FAIL: TestTape_Write (0.00s)
    tape_test.go:23: got 'abc45' want 'abc'
```

كما توقعنا! فهو يكتب البيانات التي نريدها، لكنه يترك بقية البيانات الأصلية.

## اكتب ما يكفي من الشيفرة لينجح الاختبار

للنوع `os.File` دالة اقتطاع تتيح لنا تفريغ الملف فعلياً. وينبغي أن نستطيع استدعاءها فقط للحصول على ما نريد.

غيّر `tape` إلى ما يلي:

```go
//tape.go
type tape struct {
	file *os.File
}

func (t *tape) Write(p []byte) (n int, err error) {
	t.file.Truncate(0)
	t.file.Seek(0, io.SeekStart)
	return t.file.Write(p)
}
```

سيفشل المصرِّف (compiler) في عدد من الأماكن التي نتوقع فيها `io.ReadWriteSeeker` لكننا نرسل `*os.File`. ينبغي أن تستطيع إصلاح هذه المشكلات بنفسك الآن، لكن إن علقت فراجع الشيفرة المصدرية.

وبمجرد أن تنجز إعادة الهيكلة، ينبغي أن ينجح اختبار `TestTape_Write`!

### إعادة هيكلة صغيرة أخرى

لدينا في `RecordWin` السطر `json.NewEncoder(f.database).Encode(f.league)`.

لا نحتاج إلى إنشاء مرمِّز جديد في كل مرة نكتب فيها، بل يمكننا تهيئة واحد في الدالة البانية واستعماله بدلاً من ذلك.

خزّن مرجعاً إلى `Encoder` في نوعنا وهيّئه في الدالة البانية:

```go
//file_system_store.go
type FileSystemPlayerStore struct {
	database *json.Encoder
	league   League
}

func NewFileSystemPlayerStore(file *os.File) *FileSystemPlayerStore {
	file.Seek(0, io.SeekStart)
	league, _ := NewLeague(file)

	return &FileSystemPlayerStore{
		database: json.NewEncoder(&tape{file}),
		league:   league,
	}
}
```

تنتقل `tape.Write` إلى بداية الملف في _كل_ استدعاء، لذا يستحق الأمر أن نتوقف لنتحقق من أن هذا الجمع آمن فعلاً: فلو استدعت `Encode` الطريقة `Write` أكثر من مرة في استدعاء واحد، لعادت كل عملية كتابة لاحقة إلى البداية وكتبت فوق السابقة، فتفسد المخرجات. لكنها لا تفعل ذلك، إذ تحوّل `Encoder.Encode` دائماً القيمة كاملة إلى صيغتها التسلسلية في الذاكرة أولاً، ثم تسلّمها إلى `Writer` الأساسي في استدعاء `Write` واحد، فلا تنتقل `tape` إلا مرة واحدة لكل `Encode`، وهذا بالضبط سلوك "الكتابة دائماً من البداية" الذي نريده.

استعمله في `RecordWin`.

```go
func (f *FileSystemPlayerStore) RecordWin(name string) {
	player := f.league.Find(name)

	if player != nil {
		player.Wins++
	} else {
		f.league = append(f.league, Player{name, 1})
	}

	f.database.Encode(f.league)
}
```

## ألم نخرق للتو بعض القواعد؟ اختبار أشياء خاصة؟ بلا واجهات؟

### عن اختبار الأنواع الخاصة

صحيح أنه ينبغي _عموماً_ أن تفضّل عدم اختبار الأشياء الخاصة، لأن ذلك قد يقود أحياناً إلى اقتران اختباراتك بالتنفيذ بشدة، وهذا قد يعيق إعادة الهيكلة مستقبلاً.

لكن يجب ألا ننسى أن الاختبارات ينبغي أن تمنحنا _الثقة_.

لم نكن واثقين من أن تنفيذنا سيعمل إن أضفنا أي نوع من وظائف التعديل أو الحذف. ولم نرد ترك الشيفرة هكذا، خصوصاً إن كان يعمل عليها أكثر من شخص قد لا يكون مدركاً لقصور أسلوبنا الأولي.

وأخيراً، إنه اختبار واحد فقط! فإن قررنا تغيير طريقة عمله، فلن يكون حذف الاختبار كارثة، لكننا على الأقل جسّدنا المتطلب لمن سيصونون الشيفرة مستقبلاً.

### الواجهات

بدأنا الشيفرة باستعمال `io.Reader`، لأن ذلك كان أسهل مسار لنا لاختبار `PlayerStore` الجديد باختبارات الوحدة. ومع تطويرنا للشيفرة انتقلنا إلى `io.ReadWriter` ثم `io.ReadWriteSeeker`. ثم اكتشفنا أنه لا شيء في المكتبة القياسية يحقق ذلك فعلاً باستثناء `*os.File`. وكان بإمكاننا أن نقرر كتابة واحد خاص بنا أو استعمال واحد مفتوح المصدر، لكن بدا من العملي إنشاء ملفات مؤقتة للاختبارات فحسب.

وأخيراً، احتجنا إلى `Truncate` الموجودة أيضاً في `*os.File`. وكان من الخيارات إنشاء واجهة خاصة بنا تجسّد هذه المتطلبات.

```go
type ReadWriteSeekTruncate interface {
	io.ReadWriteSeeker
	Truncate(size int64) error
}
```

لكن ما الذي يمنحنا إياه هذا حقاً؟ تذكّر أننا _لا نحاكي_، ومن غير الواقعي أن يأخذ مخزن **نظام الملفات** أي نوع غير `*os.File`، لذا لا نحتاج إلى تعدد الأشكال الذي تمنحنا إياه الواجهات.

لا تخف من تبديل الأنواع وتغييرها والتجريب كما فعلنا هنا. فالرائع في استعمال لغة ثابتة الأنواع أن المصرِّف سيساعدك مع كل تغيير.

## معالجة الأخطاء

قبل أن نبدأ العمل على الترتيب، ينبغي أن نتأكد من رضانا عن شيفرتنا الحالية ونزيل أي دَين تقني قد يكون لدينا. فمن المبادئ المهمة الوصول إلى برنامج يعمل بأسرع ما يمكن (البقاء خارج الحالة الحمراء)، لكن هذا لا يعني أن نتجاهل حالات الخطأ!

إن عدنا إلى `file_system_store.go` فسنجد في الدالة البانية `league, _ := NewLeague(file)`.

يمكن أن تعيد `NewLeague` خطأً (error) إن لم تستطع تحليل الدوري من `*os.File` الذي نقدّمه.

كان من العملي تجاهل ذلك في حينه لأن لدينا بالفعل اختبارات فاشلة. ولو حاولنا معالجته في الوقت نفسه، لكنا نتلاعب بأمرين معاً.

لنجعل الدالة البانية قادرة على إعادة خطأ.

```go
//file_system_store.go
func NewFileSystemPlayerStore(file *os.File) (*FileSystemPlayerStore, error) {
	file.Seek(0, io.SeekStart)
	league, err := NewLeague(file)

	if err != nil {
		return nil, fmt.Errorf("problem loading player store from file %s, %v", file.Name(), err)
	}

	return &FileSystemPlayerStore{
		database: json.NewEncoder(&tape{file}),
		league:   league,
	}, nil
}
```

تذكّر أن من المهم جداً إعطاء رسائل خطأ مفيدة (تماماً كما في اختباراتك). يقول الناس على الإنترنت مازحين إن معظم شيفرة غو (Go) هي:

```go
if err != nil {
	return err
}
```

**هذا ليس الأسلوب المعتاد في اللغة بنسبة 100%.** فإضافة معلومات سياقية (أي ما كنت تفعله حين حدث الخطأ) إلى رسائل الخطأ تجعل تشغيل برنامجك وإدارته أسهل بكثير.

إن حاولت التصريف فستحصل على بعض الأخطاء.

```
./main.go:18:35: multiple-value NewFileSystemPlayerStore() in single-value context
./file_system_store_test.go:35:36: multiple-value NewFileSystemPlayerStore() in single-value context
./file_system_store_test.go:57:36: multiple-value NewFileSystemPlayerStore() in single-value context
./file_system_store_test.go:70:36: multiple-value NewFileSystemPlayerStore() in single-value context
./file_system_store_test.go:85:36: multiple-value NewFileSystemPlayerStore() in single-value context
./server_integration_test.go:12:35: multiple-value NewFileSystemPlayerStore() in single-value context
```

في `main` سنريد إنهاء البرنامج مع طباعة الخطأ.

```go
//main.go
store, err := NewFileSystemPlayerStore(db)

if err != nil {
	log.Fatalf("problem creating file system player store, %v ", err)
}
```

وفي الاختبارات ينبغي أن نؤكد عدم وجود خطأ. ويمكننا صنع دالة مساعدة لذلك.

```go
//file_system_store_test.go
func assertNoError(t testing.TB, err error) {
	t.Helper()
	if err != nil {
		t.Fatalf("didn't expect an error but got one, %v", err)
	}
}
```

عالج مشكلات التصريف الأخرى باستعمال هذه الدالة المساعدة. وأخيراً، ينبغي أن يكون لديك اختبار فاشل:

```
=== RUN   TestRecordingWinsAndRetrievingThem
--- FAIL: TestRecordingWinsAndRetrievingThem (0.00s)
    server_integration_test.go:14: didn't expect an error but got one, problem loading player store from file /var/folders/nj/r_ccbj5d7flds0sf63yy4vb80000gn/T/db841037437, problem parsing league, EOF
```

لا نستطيع تحليل الدوري لأن الملف فارغ. ولم نكن نحصل على أخطاء من قبل لأننا كنا نتجاهلها دائماً.

لنصلح اختبار التكامل الكبير بوضع بعض JSON الصالح فيه:

```go
//server_integration_test.go
func TestRecordingWinsAndRetrievingThem(t *testing.T) {
	database, removeFile := createTempFile(t, `[]`)
	//etc...
}
```

والآن بعد أن نجحت كل الاختبارات، علينا معالجة سيناريو الملف الفارغ.

## اكتب الاختبار أولاً

```go
//file_system_store_test.go
t.Run("works with an empty file", func(t *testing.T) {
	database, removeFile := createTempFile(t, "")
	defer removeFile()

	_, err := NewFileSystemPlayerStore(database)

	assertNoError(t, err)
})
```

## حاول تشغيل الاختبار

```
=== RUN   TestFileSystemStore/works_with_an_empty_file
    --- FAIL: TestFileSystemStore/works_with_an_empty_file (0.00s)
        file_system_store_test.go:108: didn't expect an error but got one, problem loading player store from file /var/folders/nj/r_ccbj5d7flds0sf63yy4vb80000gn/T/db019548018, problem parsing league, EOF
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

غيّر الدالة البانية إلى ما يلي

```go
//file_system_store.go
func NewFileSystemPlayerStore(file *os.File) (*FileSystemPlayerStore, error) {

	file.Seek(0, io.SeekStart)

	info, err := file.Stat()

	if err != nil {
		return nil, fmt.Errorf("problem getting file info from file %s, %v", file.Name(), err)
	}

	if info.Size() == 0 {
		file.Write([]byte("[]"))
		file.Seek(0, io.SeekStart)
	}

	league, err := NewLeague(file)

	if err != nil {
		return nil, fmt.Errorf("problem loading player store from file %s, %v", file.Name(), err)
	}

	return &FileSystemPlayerStore{
		database: json.NewEncoder(&tape{file}),
		league:   league,
	}, nil
}
```

تعيد `file.Stat` إحصاءات عن ملفنا، مما يتيح لنا التحقق من حجم الملف. فإن كان فارغاً، نكتب بـ`Write` مصفوفة JSON فارغة، ونعود بـ`Seek` إلى البداية، استعداداً لبقية الشيفرة.

## أعد الهيكلة

صارت الدالة البانية فوضوية بعض الشيء الآن، فلنستخرج شيفرة التهيئة إلى دالة:

```go
//file_system_store.go
func initialisePlayerDBFile(file *os.File) error {
	file.Seek(0, io.SeekStart)

	info, err := file.Stat()

	if err != nil {
		return fmt.Errorf("problem getting file info from file %s, %v", file.Name(), err)
	}

	if info.Size() == 0 {
		file.Write([]byte("[]"))
		file.Seek(0, io.SeekStart)
	}

	return nil
}
```

```go
//file_system_store.go
func NewFileSystemPlayerStore(file *os.File) (*FileSystemPlayerStore, error) {

	err := initialisePlayerDBFile(file)

	if err != nil {
		return nil, fmt.Errorf("problem initialising player db file, %v", err)
	}

	league, err := NewLeague(file)

	if err != nil {
		return nil, fmt.Errorf("problem loading player store from file %s, %v", file.Name(), err)
	}

	return &FileSystemPlayerStore{
		database: json.NewEncoder(&tape{file}),
		league:   league,
	}, nil
}
```

## الترتيب

تريد مالكة المنتج أن تعيد `/league` اللاعبين مرتبين بحسب نتائجهم، من الأعلى إلى الأدنى.

القرار الأساسي هنا هو أين ينبغي أن يحدث هذا في البرنامج. فلو كنا نستعمل قاعدة بيانات "حقيقية" لاستعملنا أشياء مثل `ORDER BY` ليكون الترتيب سريعاً جداً. لهذا السبب، يبدو أن تنفيذات `PlayerStore` ينبغي أن تكون المسؤولة.

## اكتب الاختبار أولاً

يمكننا تحديث التوكيد في اختبارنا الأول في `TestFileSystemStore`:

```go
//file_system_store_test.go
t.Run("league sorted", func(t *testing.T) {
	database, removeFile := createTempFile(t, `[
		{"Name": "Cleo", "Wins": 10},
		{"Name": "Chris", "Wins": 33}]`)
	defer removeFile()

	store, err := NewFileSystemPlayerStore(database)

	assertNoError(t, err)

	got := store.GetLeague()

	want := League{
		{"Chris", 33},
		{"Cleo", 10},
	}

	assertLeague(t, got, want)

	// read again
	got = store.GetLeague()
	assertLeague(t, got, want)
})
```

ترتيب JSON الوارد خاطئ، وسيتحقق `want` من أنه يُعاد إلى المستدعي بالترتيب الصحيح.

## حاول تشغيل الاختبار

```
=== RUN   TestFileSystemStore/league_from_a_reader,_sorted
    --- FAIL: TestFileSystemStore/league_from_a_reader,_sorted (0.00s)
        file_system_store_test.go:46: got [{Cleo 10} {Chris 33}] want [{Chris 33} {Cleo 10}]
        file_system_store_test.go:51: got [{Cleo 10} {Chris 33}] want [{Chris 33} {Cleo 10}]
```

## اكتب ما يكفي من الشيفرة لينجح الاختبار

```go
func (f *FileSystemPlayerStore) GetLeague() League {
	sort.Slice(f.league, func(i, j int) bool {
		return f.league[i].Wins > f.league[j].Wins
	})
	return f.league
}
```

الدالة [`sort.Slice`](https://golang.org/pkg/sort/#Slice)

> ترتّب `Slice` الشريحة المقدّمة بحسب دالة "أصغر من" المقدّمة.

سهل!

## الخلاصة

### ما تناولناه

- الواجهة `Seeker` وعلاقتها بـ`Reader` و`Writer`.
- العمل مع الملفات.
- إنشاء دالة مساعدة سهلة الاستعمال للاختبار مع الملفات تخفي كل الأشياء الفوضوية.
- الدالة `sort.Slice` لترتيب الشرائح.
- استعمال المصرِّف لمساعدتنا على إجراء تغييرات بنيوية في التطبيق بأمان.

### خرق القواعد

- معظم القواعد في هندسة البرمجيات ليست قواعد حقاً، بل أفضل ممارسات تنجح في 80% من الأحيان.
- اكتشفنا سيناريو لم تكن فيه إحدى "قواعدنا" السابقة، وهي عدم اختبار الدوال الداخلية، مفيدة لنا، فخرقنا القاعدة.
- من المهم عند خرق القواعد أن تفهم المقايضة التي تقوم بها. ففي حالتنا لم نمانع لأنه كان اختباراً واحداً فقط، وكان سيصعب جداً اختبار السيناريو بطريقة أخرى.
- لكي تستطيع خرق القواعد **عليك أن تفهمها أولاً**. والتشبيه هنا بتعلّم الغيتار. فلا يهم مدى إبداعك في نظرك، عليك أن تفهم الأساسيات وتتمرن عليها.

### أين وصل برنامجنا

- لدينا واجهة برمجية عبر HTTP تستطيع فيها إنشاء لاعبين وزيادة نتائجهم.
- نستطيع إعادة دوري بنتائج الجميع بصيغة JSON.
- تُحفظ البيانات في ملف JSON.
