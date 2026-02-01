
'Type Kangaroo

'End Type

'Dim kanga as Kangaroo

' ====================================================
' FreeBASIC DIM test examples
' ====================================================

' 1️⃣ Yksittäiset muuttujat
Dim a As Integer
Dim b As Double
Dim c As String
Dim d As Single

' 2️⃣ Useampi muuttuja eri tyypeillä samassa rivissä
Dim x As Integer, y As Double, z As String

' 3️⃣ Useampi muuttuja samalla tyypillä, vaihtoehtoinen syntaksi
Dim As Integer i, j, k
Dim As Double px, py, pz

' 4️⃣ Muuttuja initializerilla
Dim count As Integer = 10
Dim price As Double = 3.14
Dim fame As String = "Hello"

' 5️⃣ Yksinkertaiset arrayt
Dim arr1(5) As Integer           ' 0..5 oletus
Dim arr2(0 To 5) As Double       ' rajat erikseen
Dim arr3(1 To 10) As String

' 6️⃣ Monidimensionaaliset arrayt
Dim arr4(1 To 2, 0 To 5) As Single
Dim arr5(0 To 2, 3, 5 To 8) As Integer

' 7️⃣ Array initializerit
Dim arr6(2) As Integer => {1, 2, 3}
Dim arr7(1 To 2, 1 To 2) As Integer => {{1, 2}, {3, 4}}

' 8️⃣ User Defined Type (UDT)
Type mytype
    var1 As Double
    var2 As Integer
End Type

' DIM käyttäen UDT:tä
Dim kanga As mytype
Dim myvar(0 To 2) As mytype => {(1.0, 1), (2.0, 2), (3.0, 3)}
''ei vielä dim kanga as Type

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