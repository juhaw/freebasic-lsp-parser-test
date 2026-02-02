
'Type Kangaroo

'End Type

'Dim kanga as Kangaroo

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
Dim As Integer i, j, k     ' DIM As Type – parser tukee
Dim As Double px, py, pz   ' DIM As Type useampi muuttuja

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
Dim arr_var(...) As Double                 ' DBNF tukee "..." eli dynaaminen koko

' -----------------------------
' 7️⃣ Array initializerit (DBNF uusi)
' -----------------------------
Dim arr6(2) As Integer => {1, 2, 3}                  ' Yksidimensioinen
Dim arr7(1 To 2, 1 To 2) As Integer => {{1, 2}, {3, 4}}  ' 2D array initializer
Dim myvar(0 To 2) As mytype => {(1.0, 1), (2.0, 2), (3.0, 3)}  ' UDT array initializer

' -----------------------------
' 8️⃣ User Defined Type (UDT)
' -----------------------------
Type mytype
    var1 As Double
    var2 As Integer
End Type

' DIM käyttäen UDT:tä
Dim kanga As mytype

' -----------------------------
' 9️⃣ DIM AS Type (DBNF uusi)
' -----------------------------
Type Kangaroo
    Jump as Integer
    Pouch as Integer
    hai as UByte
    'declare sub typesub()
    declare function jump_set(yksi as Integer) as Integer
    public: rotta_public as Integer
    private: rotta_private as Integer
    Static class_variable as Integer
End Type

Dim As Kangaroo kanga1, kanga2, susihukkanen  ' DIM AS Type, useampi muuttuja

' -----------------------------
' 10️⃣ SHARED muuttujat (DBNF uusi)
' -----------------------------
Dim Shared counter As Integer
Dim Shared arr(5) As Double

' -----------------------------
' 11️⃣ Suffix-pohjainen tyyppi (DBNF uusi)
' -----------------------------
Dim s$          ' String
Dim i%          ' Integer
Dim d#          ' Double
Dim f!          ' Single
Dim l&          ' LongInt

' ====================================================
' End of FreeBASIC DIM tests
' ====================================================



'==================================
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