'#include "sprite.bi"

'Dim s As Sprite

Type Kangaroo
	Jump as integer
	Pouch as integer
	hai as ubyte
	'declare sub typesub()
	declare function jump_set(yksi as integer) as integer
	public: rotta_public as integer
	private: rotta_private as integer
	Static class_variable as integer
End Type
dim as Kangaroo kanga1, kanga2, susihukkanen

kanga1.jump = kanga1.rotta_public

kanga1.jump = kanga1.jump_set(1)
kanga2.jump = kanga2.jump_set(2)
print("kanga1.jump:" & kanga1.jump)
print("kanga2.jump:" & kanga2.jump)

print("=== Freebasic End===")

function Kangaroo.jump_set(yksi as integer) as integer
	return yksi
end function