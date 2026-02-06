' ====================================================
' FreeBASIC DIM – täydellinen dokumentoitu testilista
' ====================================================

' -----------------------------
' 1️⃣ Yksittäiset muuttujat
' -----------------------------
Dim a As Integer         ' Yksittäinen Integer
Dim b As Double          ' Yksittäinen Double
Dim c As String          ' Yksittäinen String
Dim d As Single          ' Yksittäinen Single

' -----------------------------
' 2️⃣ Useampi muuttuja eri tyypeillä samassa rivissä
' -----------------------------
Dim x As Integer, y As Double, z As String  ' Useampi muuttuja, eri tyypit

' -----------------------------
' 3️⃣ Useampi muuttuja samalla tyypillä, vaihtoehtoinen syntaksi (DBNF uusi)
' -----------------------------
Dim i As Integer, j As Integer, k As Integer     ' DIM As Type – parser tukee
Dim px As Double, py As Double, pz As Double    ' DIM As Type useampi muuttuja

' -----------------------------
' 4️⃣ Muuttuja initializerilla
' -----------------------------
Dim count As Integer = 10          ' Yksittäinen muuttuja + initializer
Dim price As Double = 3.14         ' Double + initializer
Dim fame As String = "Hello"       ' String + initializer

' -----------------------------
' 5️⃣ Yksinkertaiset arrayt
' -----------------------------
Dim arr1(5) As Integer            ' Array 0..5 oletus
Dim arr2(0 To 5) As Double        ' Array rajat määritelty erikseen
Dim arr3(1 To 10) As String       ' Array 1..10

' -----------------------------
' 6️⃣ Monidimensionaaliset arrayt
' -----------------------------
Dim arr4(1 To 2, 0 To 5) As Single
Dim arr5(0 To 2, 3, 5 To 8) As Integer    ' DBNF tukee epäsäännöllisiä rajauksia
Dim arr_var(10) As Double                 ' korvattu kiinteällä koolla

' -----------------------------
' 7️⃣ Array initializerit
' -----------------------------
Dim arr6(2) As Integer
arr6(0) = 1
arr6(1) = 2
arr6(2) = 3

Dim arr7(1 To 2, 1 To 2) As Integer
arr7(1,1) = 1
arr7(1,2) = 2
arr7(2,1) = 3
arr7(2,2) = 4

Type mytype
    var1 As Double
    var2 As Integer
End Type

Dim myvar(0 To 2) As mytype
myvar(0).var1 = 1.0 : myvar(0).var2 = 1
myvar(1).var1 = 2.0 : myvar(1).var2 = 2
myvar(2).var1 = 3.0 : myvar(2).var2 = 3

' -----------------------------
' 8️⃣ User Defined Type (UDT)
' -----------------------------
Type mytype2
    var1 As Double
    var2 As Integer
End Type

' DIM käyttäen UDT:tä
Dim kanga As mytype2

' -----------------------------
' 9️⃣ DIM AS Type (DBNF uusi) muutettu yksittäisiksi
' -----------------------------
Type Kangaroo
    Jump as Integer
    Pouch as Integer
    hai as UByte
    marx as integer
    
    declare sub jump_set(yksi as Integer)
    declare function jump_get() as Integer
    public: rotta_public as Integer
   
    Static class_variable as Integer

    ' Constructor: olio luodaan
    Declare Constructor(zippo As Integer)
    ' Destructor: olio tuhoutuu
    Declare Destructor()
    
    private:
    rotta_private as Integer

End Type

Dim kanga1 As Kangaroo = Kangaroo(1)
Dim kanga2 As Kangaroo = Kangaroo(2)
Dim susihukkanen As Kangaroo = Kangaroo(3)
kanga1.jump_set(5)
print "kanga1.Pouch:", kanga1.Pouch
' -----------------------------
' 10️⃣ SHARED muuttujat
' -----------------------------
Dim Shared counter As Integer
Dim Shared arr(5) As Double

'declare
sub Kangaroo.jump_set(yksi as integer)
    This.Jump = yksi
end sub

function Kangaroo.jump_get() as integer
    return This.Jump
end function



Constructor Kangaroo(zippo As Integer)
    This.marx = 5
End Constructor

Destructor Kangaroo()
    Print "Muisti vapautettu!"
End Destructor

' ====================================================
' End of FreeBASIC DIM tests
' ====================================================

print("End of Freebasic Dim")

'#include "sprite.bi"

'Dim s As Sprite

' Type Kangaroo
' 	Jump as integer
' 	Pouch as integer
' 	hai as ubyte
' 	'declare sub typesub()
' 	declare function jump_set(yksi as integer) as integer
' 	public: rotta_public as integer
' 	private: rotta_private as integer
' 	Static class_variable as integer
' End Type
' dim as Kangaroo kanga1, kanga2, susihukkanen

' kanga1.jump = kanga1.rotta_public

' kanga1.jump = kanga1.jump_set(1)
' kanga2.jump = kanga2.jump_set(2)
' print("kanga1.jump:" & kanga1.jump)
' print("kanga2.jump:" & kanga2.jump)

' print("=== Freebasic End===")

' function Kangaroo.jump_set(yksi as integer) as integer
' 	return yksi
' end function