// TritonECU — BenchSupply
// The bench power-supply enclosure, forked from TritonECU/hardware/psu-enclosure
// as the version to GROW: the supply is the first occupant, not the only one.
// The wiring bay was the room left for that, and the first thing to take some
// of it is the DC-DC module below — 5 V for the VR rig's Pico off the 36 V
// supply, plus an adjustable bench rail. What is left of the bay, and the space
// over the supply under the rim band, is still free.
//
// Mains inside a printed box. Read the safety note in README.md before you
// energise it: the lid screws are the only thing between a finger and 120 V.
//
//   render one part at a time:  part = "tub" | "lid" | "shield" | "assembly"

part = "assembly";

/* Tessellation. Same reasoning as the VR rig: chord error is r*(1-cos(180/n)),
   so a 3.2 mm hole at fn 16 is off by 0.03 mm — below what the printer
   resolves. Spend facets only where a fit depends on them. The grid is cubes,
   which cost no facets at all, so it can be as dense as it likes. */
$fn      = 32;   // general
hole_fn  = 16;   // screw clearance and pilot holes
fit_fn   = 64;   // fan bore and guard, cable gland

/* ---------------------------------------------------------------------------
   MEASURE THESE before printing — everything else is derived from them
   --------------------------------------------------------------------------- */
psu_l           = 266;   // MEASURE: supply length  (the 266 minimum)
psu_w           = 153;   // MEASURE: supply width   (the 153 minimum)
psu_h           =  77;   // MEASURE: supply height  (the 77 minimum)

/* The supply's own mounting holes. There is no standard pattern, so the default
   below is THREE PADS A SIDE AT SENSIBLE PLACES, not a real bolt circle — they
   hold the supply up off the floor for airflow and nothing more. Measure the
   feet, edit standoff_xy, then set standoff_hole = true. */
standoff_hole   = false; // MEASURE the foot pattern first, then turn this on
standoff_screw  =   4.3; // M4 clearance
standoff_cbore  =   9.0; // head recess on the OUTSIDE of the floor
standoff_cbore_h=   2.6;
standoff_d      =  12;
standoff_h      =   4;   // the air gap under the supply

/* ---------------------------------------------------------------------------
   Shell
   --------------------------------------------------------------------------- */
wall     = 3;
/* DOUBLED from 3 for the toroidal transformers. Not for strength - the stress
   was never near anything, even at 3 mm. For stiffness: 5.8 kg of iron bows a
   3 mm floor 2.1 mm, which a box standing on four rubber feet rocks on, and
   creep settles that bow in permanently. 6 mm is 8x the stiffness and gets it
   to 0.27 mm. docs/calc/floor.py has the arithmetic.
   It does NOT fix the bolt: each toroid still hangs off one central screw, and
   that is a bearing problem. Put a steel spreader under the floor. */
floor_t  = 6;
lid_t    = 5;

/* Clearances. The fan end gets a real plenum: a 40 mm fan blowing into a 3 mm
   slot just stalls against the end of the supply. 10 mm lets the air turn and
   split between the 4 mm gap under the supply and the space over it. */
clr_fan  = 10;   // plenum, fan end
clr_grid =  3;   // exhaust end
/* The BACK long wall. It used to be 3 mm - the wall the supply was simply
   pressed against, and the only wall in the box with nothing in it. The mains
   inlet has moved onto it, so it now has to hold the inlet's 24 mm of flange
   and terminals plus the shield over them: 31.5 mm, and 34 leaves 2.5 mm to
   the supply.

   It is cheaper here than it was at END B. There the shield's 44 mm WIDTH had
   to fit across the bay; on a long wall the width runs along the wall, which
   is free, so only the depth costs anything. 50 at END B, 34 here. */
bay_back = 34;

/* The wiring bay. It used to be 39, set by the IEC module's rear flange on the
   long side. The plug has since moved to END B, and what sets the width now is
   the SHIELD over its terminals: 29 mm of flange, clearance for booted spades
   either side, and a wall each side comes to 44, which a 39 mm bay cannot hold.

   50 costs 11 mm of box width and gives it back twice over — with the plug off
   the long side there is 24.6 mm behind the DC-DC without any boss at all, so
   mod_boss goes to 0 and the external bump on that wall disappears. The bed
   footprint is unchanged either way. */
bay_w    = 50;

/* ---------------------------------------------------------------------------
   Lid seat
   ---------------------------------------------------------------------------
   The lid screws CANNOT land in corner posts: with 3 mm of clearance beside the
   supply there is nowhere to put a post. So the screws go into a band that
   thickens the wall inward around the whole top rim, sitting entirely ABOVE the
   supply where the volume is free anyway. The band's underside is a 45 degree
   taper (rim_taper = rim_w), so it prints with no support and no drooping
   ledge, and its inner face doubles as the rabbet the lid locates in. */
rim_w     = 6;       // how far the band comes inward
rim_taper = rim_w;   // 45 degrees. Keep these equal.
head      = 2;       // gap between the supply's top and the start of the taper
boss_d    = 9;       // screw engagement depth in the band
lid_screw = 2.6;     // M3 cutting its own thread. Heat-set insert? use 4.2.
lid_clr   = 3.4;     // M3 clearance through the lid
lid_cbore = 6.4;     // socket head recess
lid_cbore_h = 3.2;

/* ---------------------------------------------------------------------------
   Derived box
   --------------------------------------------------------------------------- */
in_l  = clr_fan + psu_l + clr_grid;
in_w  = bay_back + psu_w + bay_w;
in_h  = standoff_h + psu_h + head + rim_taper + boss_d;

out_l = in_l + 2*wall;   // 285
out_w = in_w + 2*wall;   // 201
out_h = floor_t + in_h;  // 101

/* Supply's own corner, in box coordinates. */
psu_x0 = wall + clr_fan;
psu_y0 = wall + bay_back;
psu_z0 = floor_t + standoff_h;
psu_top = psu_z0 + psu_h;

rim_z0 = psu_top + head;      // taper starts
rim_z1 = rim_z0 + rim_taper;  // band is full width from here up

standoff_xy = [ for (x = [psu_x0 + 12, psu_x0 + psu_l/2, psu_x0 + psu_l - 12],
                     y = [psu_y0 + 12, psu_y0 + psu_w - 12]) [x, y] ];

/* ---------------------------------------------------------------------------
   40 x 40 x 10 fan — END A (x = 0), blowing IN
   ---------------------------------------------------------------------------
   Mounted OUTSIDE the wall. Inside would cost 10 mm of a 10 mm plenum and the
   supply is only 10 mm away. The pad gives the M3s 8 mm of plastic to cut into
   instead of 3, and its underside is drafted at 45 so it needs no support. */
fan_sq       = 40;
fan_pitch    = 32;    // bolt centres, from the drawing
fan_screw    =  2.6;  // M3 self-tapping through the fan's own 3.5 mm holes
fan_bore     = 38;
fan_pad      = 46;
fan_pad_t    =  5;
fan_guard    = true;  // concentric webs over the bore
fan_web      =  2.0;

fan_cy = psu_y0 + psu_w/2;
fan_cz = psu_z0 + psu_h/2;

/* ---------------------------------------------------------------------------
   Exhaust grid — END B (x = out_l)
   ---------------------------------------------------------------------------
   Squares turned 45 degrees. A square hole in a vertical wall has a flat top
   edge that has to bridge; a diamond has an apex, so every hole is
   self-supporting and there is nothing to droop into the airstream. */
grid_pitch = 10;
grid_sq    =  6;   // side. Across the corners that is 8.49, leaving 1.5 of rib.
grid_inset =  8;   // keep the grid inside the supply's shadow

/* ---------------------------------------------------------------------------
   IEC C14 inlet / switch / fuse module — BACK WALL (y = 0)
   ---------------------------------------------------------------------------
   Moved again, and this is where it belongs: the back long wall is the one
   surface with nothing else on it, so the mains gets a wall to itself and the
   front wall is all low voltage - the DC-DC's screen, its knob, the outputs.
   Cord out the back, controls at the front.

   That wall was blank because it had no depth; bay_back is what buys it. END B
   goes back to being nothing but exhaust grid, which is better for the air.

   Still 58 mm axis VERTICAL, so the rocker is at the top and the fuse drawer
   pulls out below it. Low, because the shield stands on the floor and uses the
   floor as the fourth side of its wire slot. */
plug_cut_l     = 50;   // flange, along Z
plug_cut_w     = 29;   // flange, along X
plug_clr       =  0.6;
plug_hole_pitch= 40;   // ear centres, along X
plug_hole_d    =  3.2;
plug_pad_w     = 54;   // along the wall. Bezel is 48 - pad it out
plug_pad_z     = 64;   // bezel is 58 tall
plug_pad_t     =  4;   // 4 + 3 = 7 mm of thread for the ear screws

plug_x = out_l/2;      // CENTRED: a toroid sits either side of it, so the
                       // primary leads reach it from both without crossing
plug_z = 36;           // low, so the shield reaches the floor

/* How far the flange and its terminals reach INSIDE from the wall's inner
   face. The pad eats 7 mm of the 19 mm flange, so 12 intrudes, and the booted
   spades add 12 behind that. This is what the shield has to cover. */
plug_reach = 12 + 12;

/* DC output. PG7 gland or a rubber grommet; same wall, same bay. */
gland_d =  12.5;
gland_x = out_l - 105;   // clear of the shield, which owns the END B end now
gland_z = psu_z0 + psu_h/2;

/* ---------------------------------------------------------------------------
   DC-DC module — LONG SIDE (y = out_w), END A end of the bay
   ---------------------------------------------------------------------------
   A second supply, but not a second mains supply: it hangs off the 36 V output
   of the one already in the box. Two rails — a fixed 5 V that runs the Pico and
   the DM542's opto commons, and an adjustable rail set from its own LCD.

   It is held by ITS OWN SNAP LOCKS and nothing else. The two tapered locks
   start about 1 mm behind the bezel and taper back 3, so they grip a panel
   roughly 1-4 mm thick. A 3 mm wall sits at the very end of that taper, which
   is a loose grip on a module standing 25 mm off the panel — so the panel is
   thinned locally to mod_panel_t and the lock bites mid-taper. That relief is
   cut on the INSIDE face, so the outside stays flat and the bezel lands on
   plain wall.

   MEASURE every value marked below. The one that is a DECISION rather than a
   measurement is mod_boss, and it changes the shape of the box. */
mod_cut_w   = 64;      // MEASURE: body through the panel, along X
mod_cut_h   = 38.5;    // MEASURE: body through the panel, along Z
mod_depth   = 25.4;    // MEASURE: how far it stands behind the panel
mod_flange  = 4;       // MEASURE: bezel lip beyond the cutout, all round
mod_cut_clr = 0.4;     // a snap lock wants the cutout tight, not generous
mod_panel_t = 2.0;     // local panel at the cutout, for the snap locks to bite

/* Two locks, one on each VERTICAL edge of the cutout, centred in Z. So the
   surfaces that actually carry the module are the cutout's left and right
   edges — which, with the tub printed floor-down, are vertical walls in the
   print and come out crisp. Nothing may intrude on those edges, and the relief
   below has to reach past them. */
mod_lock_w  = 12.7;    // MEASURE: each lock, along Z
mod_relief_m= 6;       // how far the thinned panel reaches past the cutout

/* The bay is 39 wide and the module eats 25.4 of it, leaving 13.6 for its
   terminals and the bend in the wire — not enough if the terminals exit
   straight back, which on these modules they usually do. So the panel steps
   OUTWARD on a drafted boss: 12 mm buys 25.6 mm of clear bay behind the module
   and costs 12 mm of bed in Y, which a 300 bed has to spare (X is the tight
   axis here, not Y).

   With the plug gone to END B the bay went to 50, which leaves 24.6 mm behind
   the module on a FLAT wall — so the boss is no longer needed and mod_boss is
   0. Raise it again if you narrow the bay. Decide BEFORE printing. */
mod_boss    = 0;

mod_x       = 64;                // clear of the plug pad, END A end of the bay
mod_z       = psu_z0 + psu_h/2;  // same centreline as the plug and the gland
mod_face_y  = out_w + mod_boss;  // the panel the module snaps into

/* Boss outline: bezel footprint, plus a wall each side, plus a little margin. */
mod_bw = mod_cut_w + 2*mod_flange + 2*wall + 6;
mod_bh = mod_cut_h + 2*mod_flange + 2*wall + 6;

/* Low-voltage output — END A, in the bay's corner.
   Deliberately NOT on the plug wall: it keeps the 5 V and adjustable rails from
   running the length of the bay alongside the mains terminals. */
lv_gland_d = 12.5;
lv_gland_y = psu_y0 + psu_w + bay_w/2;
lv_gland_z = mod_z;

/* ---------------------------------------------------------------------------
   Checks — the module was dropped into a wall that already had two things on it
   ---------------------------------------------------------------------------
   These are the clearances that were tight enough to be worth arithmetic rather
   than a look at the preview. They fire at render time, so changing mod_x,
   mod_boss or the bay tells you immediately instead of after a 14 hour print. */
mod_clear_behind = bay_w + mod_boss - mod_depth;

assert(mod_clear_behind > 8,
       "DC-DC module: not enough bay left behind it for terminals. Raise mod_boss.");
assert(mod_x + mod_bw/2 < out_l - wall && mod_x - mod_bw/2 > wall,
       "DC-DC runs off the end of the bay wall. Move mod_x.");
assert(abs(mod_x - gland_x) > mod_bw/2 + gland_d,
       "DC-DC runs into the DC output gland. Move mod_x or gland_x.");
/* The boss's cavity floor drafts up toward the panel at 45 degrees; it has to
   stay below the bottom of the module's body or it fouls it. */
assert(mod_z - (mod_bh - 2*wall)/2 < mod_z - mod_cut_h/2 - 2,
       "DC-DC boss is too shallow in Z - its drafted floor fouls the module.");
assert(mod_panel_t >= 1 && mod_panel_t <= 4,
       "DC-DC panel is outside the snap lock's 1-4 mm grip range.");
/* The locks ride the cutout's vertical edges, so the thinned panel has to
   extend past those edges — and stay inside the boss, or it breaks through. */
assert(mod_relief_m >= 3,
       "Thinned panel does not reach past the cutout edges the snap locks ride.");
assert(mod_cut_w + 2*mod_relief_m < mod_bw - 2*wall &&
       mod_cut_h + 2*mod_relief_m < mod_bh - 2*wall || mod_boss == 0,
       "Panel relief is wider than the boss it is cut into.");
assert(mod_lock_w < mod_cut_h,
       "Snap lock is longer than the edge it sits on - check mod_cut_h.");
/* The boss is on the OUTSIDE, so what bounds it is the wall itself: the lid
   line above, the floor below. Its skirt reaches mod_boss lower than its face. */
assert(mod_z + mod_bh/2 < out_h && mod_z - mod_bh/2 - mod_boss > 0,
       "DC-DC boss runs off the wall in Z.");
assert(lv_gland_y - lv_gland_d/2 > psu_y0 + psu_w,
       "LV gland is in the supply's shadow, not the bay.");

/* --- the inlet and its shield, on the BACK wall -------------------------- */
/* The pad is a slab on the OUTSIDE: run it off the end of the wall and it
   hangs in mid-air with nothing behind it. */
assert(plug_x + plug_pad_w/2 <= out_l && plug_x - plug_pad_w/2 >= 0,
       "Inlet pad overhangs the end of the back wall. Move plug_x.");
assert(plug_hole_pitch < plug_pad_w,
       "Inlet ear screws fall outside their own pad.");
assert(plug_z - plug_pad_z/2 > 0 && plug_z + plug_pad_z/2 < out_h,
       "Inlet pad runs off the wall in Z.");
/* The shield stands on the floor between the wall and the supply. */
assert(sh_y1 + sh_wall < psu_y0,
       "Shield is deeper than the back bay. Raise bay_back or cut sh_clr.");
assert(sh_z1 + sh_wall < rim_z0,
       "Shield is taller than the box's clear height - lower plug_z.");
assert(sh_notch_w < sh_x1 - sh_x0,
       "Wire slot is wider than the shield's back face.");
assert(sh_notch_h < sh_tab_z - floor_t,
       "Wire slot runs into the screw tabs. Raise sh_tab_z.");
assert(sh_tab_x[0] - sh_post_d/2 > wall && sh_tab_x[1] + sh_post_d/2 < out_l - wall,
       "Shield tabs or posts run off the end of the bay.");
assert(sh_tab_y + sh_post_d/2 < psu_y0,
       "Shield posts are under the supply.");

/* ---------------------------------------------------------------------------
   TUB
   --------------------------------------------------------------------------- */
module cavity() {
    // straight sided up to the taper
    translate([wall, wall, floor_t]) cube([in_l, in_w, rim_z0 - floor_t]);
    // the 45 degree underside of the rim band
    hull() {
        translate([wall, wall, rim_z0]) cube([in_l, in_w, 0.01]);
        translate([wall + rim_w, wall + rim_w, rim_z1])
            cube([in_l - 2*rim_w, in_w - 2*rim_w, 0.01]);
    }
    // the band itself, and out through the top
    translate([wall + rim_w, wall + rim_w, rim_z1])
        cube([in_l - 2*rim_w, in_w - 2*rim_w, out_h - rim_z1 + 1]);
    // the bay, carried out into the module's boss
    mod_boss_cavity();
}

module fan_pad_solid() {
    hull() {
        translate([-0.01, fan_cy - fan_pad/2, fan_cz - fan_pad/2])
            cube([0.01, fan_pad, fan_pad]);
        translate([-fan_pad_t, fan_cy - fan_pad/2, fan_cz - fan_pad/2 + fan_pad_t])
            cube([0.01, fan_pad, fan_pad - fan_pad_t]);
    }
}

module fan_webs() {
    h = fan_pad_t + wall + 2;
    translate([-fan_pad_t - 1, fan_cy, fan_cz]) rotate([0, 90, 0]) {
        for (r = [6.5, 13])
            difference() {
                cylinder(r = r + fan_web/2, h = h, $fn = fit_fn);
                translate([0, 0, -1]) cylinder(r = r - fan_web/2, h = h + 2, $fn = fit_fn);
            }
        for (a = [45, 135])
            rotate([0, 0, a]) translate([-fan_web/2, -fan_bore/2, 0])
                cube([fan_web, fan_bore, h]);
    }
}

module fan_cuts() {
    h = fan_pad_t + wall + 2;
    difference() {
        translate([-fan_pad_t - 1, fan_cy, fan_cz]) rotate([0, 90, 0])
            cylinder(d = fan_bore, h = h, $fn = fit_fn);
        if (fan_guard) fan_webs();
    }
    for (dy = [-1, 1], dz = [-1, 1])
        translate([-fan_pad_t - 1, fan_cy + dy*fan_pitch/2, fan_cz + dz*fan_pitch/2])
            rotate([0, 90, 0]) cylinder(d = fan_screw, h = h, $fn = hole_fn);
}

module grid_cuts() {
    gw = psu_w - 2*grid_inset;
    gh = psu_h - 2*grid_inset;
    ny = floor(gw / grid_pitch);
    nz = floor(gh / grid_pitch);
    cy = psu_y0 + psu_w/2;
    cz = psu_z0 + psu_h/2;
    for (i = [0 : ny - 1], j = [0 : nz - 1])
        translate([out_l - wall/2,
                   cy + (i - (ny - 1)/2) * grid_pitch,
                   cz + (j - (nz - 1)/2) * grid_pitch])
            rotate([45, 0, 0]) cube([wall + 2, grid_sq, grid_sq], center = true);
}

module plug_pad_solid() {
    x0 = plug_x - plug_pad_w/2;
    z0 = plug_z - plug_pad_z/2;
    hull() {
        translate([x0, 0.01, z0]) cube([plug_pad_w, 0.01, plug_pad_z]);
        translate([x0, -plug_pad_t, z0 + plug_pad_t])
            cube([plug_pad_w, 0.01, plug_pad_z - plug_pad_t]);
    }
}

module plug_cuts() {
    d = wall + plug_pad_t + 2;
    translate([plug_x - (plug_cut_w + plug_clr)/2,
               -plug_pad_t - 1,
               plug_z - (plug_cut_l + plug_clr)/2])
        cube([plug_cut_w + plug_clr, d, plug_cut_l + plug_clr]);
    for (dx = [-1, 1])
        translate([plug_x + dx*plug_hole_pitch/2, -plug_pad_t - 1, plug_z])
            rotate([-90, 0, 0]) cylinder(d = plug_hole_d, h = d, $fn = hole_fn);
}

/* ---------------------------------------------------------------------------
   MAINS SHIELD — a hood over the back of the inlet
   ---------------------------------------------------------------------------
   The inlet's spade terminals are the only exposed mains inside this box. With
   the lid off they are a finger away. This covers them.

   A cup with TWO open faces: the one against the back wall, where the inlet
   comes through, and the BOTTOM, where it stands on the floor.

   The wire slot is the whole point of the shape. The three spades are crimped
   and booted before the shield goes near them, so the wires cannot be threaded
   through a closed hole - the hole has to be open on one side and closed by
   something else afterwards. So the slot runs off the bottom edge of the back
   face: THREE of its sides are printed, and the FOURTH is the enclosure floor
   once the shield is screwed down.

   Its screw tabs reach SIDEWAYS, not backwards. Backwards would put the posts
   under a toroid; along the wall there is nothing but wall.

   Print it on its back, the slotted face flat on the bed. Every other wall is
   then perpendicular to the bed and there is not one overhang in the part. */
sh_clr     = 5;      // around the inlet's envelope, for the boots
sh_wall    = 2.5;
sh_notch_w = 26;     // three booted spades side by side
sh_notch_h = 14;     // up from the floor
sh_tab_z   = floor_t + 17;  // above the notch, which starts at the floor
sh_tab_t   = 3.5;
sh_tab_l   = 12;
sh_screw   = 3.2;    // M3 clearance through the tab
sh_post_d  = 9;
sh_post_p  = 2.6;    // M3 cutting its own thread

/* Cavity: everything the inlet occupies inside, plus clearance. */
sh_y0 = wall;                                   // against the back wall
sh_y1 = sh_y0 + plug_reach + sh_clr;            // back face of the cup, inside
sh_x0 = plug_x - (plug_cut_w/2 + sh_clr);
sh_x1 = plug_x + (plug_cut_w/2 + sh_clr);
sh_z1 = plug_z + plug_cut_l/2 + sh_clr;         // roof, inside
sh_tab_y = (sh_y0 + sh_y1)/2;                   // tabs at mid-depth
sh_tab_x = [sh_x0 - sh_wall - sh_tab_l/2, sh_x1 + sh_wall + sh_tab_l/2];

module shield_posts() {
    for (x = sh_tab_x)
        translate([x, sh_tab_y, floor_t])
            cylinder(d = sh_post_d, h = sh_tab_z - floor_t);
}

module shield_post_holes() {
    for (x = sh_tab_x)
        translate([x, sh_tab_y, sh_tab_z - 8])
            cylinder(d = sh_post_p, h = 9, $fn = hole_fn);
}

module shield() {
    tw = sh_post_d + 3;
    difference() {
        union() {
            // the cup: open at -y (the wall closes it) and -z (the floor does)
            difference() {
                translate([sh_x0 - sh_wall, sh_y0, floor_t])
                    cube([(sh_x1 - sh_x0) + 2*sh_wall,
                          (sh_y1 - sh_y0) + sh_wall,
                          (sh_z1 - floor_t) + sh_wall]);
                translate([sh_x0, sh_y0 - 1, floor_t - 1])
                    cube([sh_x1 - sh_x0, (sh_y1 - sh_y0) + 1, (sh_z1 - floor_t) + 1]);
            }
            // screw tabs, reaching sideways over the posts
            translate([sh_x1, sh_tab_y - tw/2, sh_tab_z])
                cube([sh_wall + sh_tab_l, tw, sh_tab_t]);
            translate([sh_x0 - sh_wall - sh_tab_l, sh_tab_y - tw/2, sh_tab_z])
                cube([sh_wall + sh_tab_l, tw, sh_tab_t]);
        }
        // the wire slot: open at the bottom, so the floor is its fourth side
        translate([plug_x - sh_notch_w/2, sh_y1 - 1, floor_t - 1])
            cube([sh_notch_w, sh_wall + 2, sh_notch_h + 1]);
        // tab clearance holes
        for (x = sh_tab_x)
            translate([x, sh_tab_y, sh_tab_z - 1])
                cylinder(d = sh_screw, h = sh_tab_t + 2, $fn = hole_fn);
    }
}

module gland_cut() {
    translate([gland_x, out_w - wall - 1, gland_z])
        rotate([-90, 0, 0]) cylinder(d = gland_d, h = wall + 2, $fn = fit_fn);
}

/* The boss the module's panel sits on. Drafted 45 degrees on its UNDERSIDE —
   wider at the wall, narrower at the face — so it grows out of a vertical wall
   with nothing to support. The sides are vertical planes and the top is flat,
   both of which print as they are. */
module mod_boss_solid() {
    if (mod_boss > 0) {
        x0 = mod_x - mod_bw/2;
        z0 = mod_z - mod_bh/2;
        hull() {
            translate([x0, out_w - 0.01, z0 - mod_boss])
                cube([mod_bw, 0.01, mod_bh + mod_boss]);
            translate([x0, mod_face_y, z0]) cube([mod_bw, 0.01, mod_bh]);
        }
    }
}

/* ...and the bay carried out into it, leaving 3 mm of wall all round. The
   ceiling is a 3-sided bridge only mod_boss deep, which any printer manages. */
module mod_boss_cavity() {
    if (mod_boss > 0) {
        cw = mod_bw - 2*wall;
        ch = mod_bh - 2*wall;
        x0 = mod_x - cw/2;
        z0 = mod_z - ch/2;
        hull() {
            translate([x0, out_w - wall - 1, z0 - mod_boss])
                cube([cw, 0.01, ch + mod_boss]);
            translate([x0, mod_face_y - wall, z0]) cube([cw, 0.01, ch]);
        }
    }
}

/* Thin the panel from the inside so the snap locks bite mid-taper. */
module mod_panel_relief() {
    pw = mod_cut_w + 2*mod_relief_m;
    ph = mod_cut_h + 2*mod_relief_m;
    d  = wall - mod_panel_t;
    translate([mod_x - pw/2, mod_face_y - wall - 0.01, mod_z - ph/2])
        cube([pw, d + 0.01, ph]);
}

module mod_cuts() {
    translate([mod_x - (mod_cut_w + mod_cut_clr)/2,
               mod_face_y - wall - 2,
               mod_z - (mod_cut_h + mod_cut_clr)/2])
        cube([mod_cut_w + mod_cut_clr, wall + 4, mod_cut_h + mod_cut_clr]);
}

module lv_gland_cut() {
    translate([-1, lv_gland_y, lv_gland_z])
        rotate([0, 90, 0]) cylinder(d = lv_gland_d, h = wall + 2, $fn = fit_fn);
}

/* Screw stations, on the centreline of wall + rim band. */
lid_inset = (wall + rim_w)/2;
lid_screws = concat(
    [ for (x = [16, out_l/3, 2*out_l/3, out_l - 16],
           y = [lid_inset, out_w - lid_inset]) [x, y] ],
    [ [lid_inset, out_w/2], [out_l - lid_inset, out_w/2] ]);

module lid_screw_blind() {
    for (p = lid_screws)
        translate([p[0], p[1], out_h - boss_d])
            cylinder(d = lid_screw, h = boss_d + 1, $fn = hole_fn);
}

module standoffs() {
    for (p = standoff_xy)
        translate([p[0], p[1], floor_t]) cylinder(d = standoff_d, h = standoff_h);
}

module standoff_holes() {
    if (standoff_hole)
        for (p = standoff_xy) {
            translate([p[0], p[1], -1])
                cylinder(d = standoff_screw, h = floor_t + standoff_h + 2, $fn = hole_fn);
            translate([p[0], p[1], -0.01])
                cylinder(d = standoff_cbore, h = standoff_cbore_h, $fn = hole_fn);
        }
}

module tub() {
    difference() {
        union() {
            difference() {
                union() {
                    cube([out_l, out_w, out_h]);
                    fan_pad_solid();
                    plug_pad_solid();
                    mod_boss_solid();
                }
                cavity();
            }
            standoffs();
            shield_posts();
        }
        fan_cuts();
        grid_cuts();
        plug_cuts();
        gland_cut();
        mod_cuts();
        mod_panel_relief();
        lv_gland_cut();
        lid_screw_blind();
        standoff_holes();
        shield_post_holes();
    }
}

/* ---------------------------------------------------------------------------
   LID
   ---------------------------------------------------------------------------
   Modelled ribs-down, as it sits on the box. PRINT IT FLIPPED, outer face on
   the bed: then every rib grows upward and nothing overhangs but the 1.5 mm
   annular bridge over each counterbore. */
stiff_h = 8;
stiff_t = 3;
loc_h   = 3;    // locating rib, into the rim opening
loc_t   = 3;
loc_clr = 0.3;

module lid() {
    ox = wall + rim_w;   // rim opening inset
    difference() {
        union() {
            translate([0, 0, stiff_h]) cube([out_l, out_w, lid_t]);
            // locating rib: a ring that drops into the rabbet
            translate([ox + loc_clr, ox + loc_clr, stiff_h - loc_h])
                linear_extrude(loc_h) difference() {
                    square([out_l - 2*(ox + loc_clr), out_w - 2*(ox + loc_clr)]);
                    translate([loc_t, loc_t])
                        square([out_l - 2*(ox + loc_clr + loc_t),
                                out_w - 2*(ox + loc_clr + loc_t)]);
                }
            // stiffeners — a 285 x 201 flat plate will bow otherwise
            for (x = [out_l/4, out_l/2, 3*out_l/4])
                translate([x - stiff_t/2, ox + 4, 0])
                    cube([stiff_t, out_w - 2*(ox + 4), stiff_h]);
            translate([16, out_w/2 - stiff_t/2, 0])
                cube([out_l - 32, stiff_t, stiff_h]);
        }
        for (p = lid_screws) {
            translate([p[0], p[1], stiff_h - 1])
                cylinder(d = lid_clr, h = lid_t + 2, $fn = hole_fn);
            translate([p[0], p[1], stiff_h + lid_t - lid_cbore_h])
                cylinder(d = lid_cbore, h = lid_cbore_h + 1, $fn = hole_fn);
        }
    }
}

/* ---------------------------------------------------------------------------
   Part selection
   --------------------------------------------------------------------------- */
/* Ghosts. Not printed — they are the check that the bay is deep enough and the
   fan clears the lid. The plug ghost is the part that matters: 19 mm of flange
   plus the spade terminals and their boots is what set bay_w in the first
   place. */
module ghost_plug() {
    f = -plug_pad_t;                                          // the pad's face
    translate([plug_x - 24, f - 5, plug_z - 29]) cube([48, 5, 58]);      // bezel
    translate([plug_x - 14.5, f, plug_z - 25]) cube([29, 19, 50]);       // flange
    translate([plug_x - 14.5, f + 19, plug_z - 25]) cube([29, 12, 50]);  // terminals
}
module ghost_fan() {
    translate([-fan_pad_t - 10, fan_cy - 20, fan_cz - 20]) cube([10, 40, 40]);
}
/* The DC-DC module: body behind the panel, bezel in front. The body is the
   check that matters — how much bay is left behind it for the terminals. */
module ghost_mod() {
    translate([mod_x - mod_cut_w/2, mod_face_y - mod_depth, mod_z - mod_cut_h/2])
        cube([mod_cut_w, mod_depth, mod_cut_h]);
    translate([mod_x - (mod_cut_w + 2*mod_flange)/2, mod_face_y,
               mod_z - (mod_cut_h + 2*mod_flange)/2])
        cube([mod_cut_w + 2*mod_flange, 3, mod_cut_h + 2*mod_flange]);
}

if      (part == "tub") tub();
else if (part == "lid") lid();
else if (part == "shield") shield();
else {
    color("lightsteelblue") tub();
    color("gainsboro") translate([0, 0, out_h - stiff_h]) lid();
    color("indianred") shield();
    // the supply itself — a ghost, to check nothing grows into it
    %translate([psu_x0, psu_y0, psu_z0]) cube([psu_l, psu_w, psu_h]);
    %ghost_plug();
    %ghost_fan();
    %ghost_mod();
}

echo(str("external  ", out_l, " x ", out_w, " x ", out_h + lid_t,
         "   (bed footprint ", out_l + fan_pad_t + plug_pad_t, " x ",
         out_w + mod_boss, ")"));
echo(str("interior  ", in_l, " x ", in_w, " x ", in_h,
         "   clear for the supply ", in_l, " x ", psu_w, " x ", psu_h + head));
echo(str("bays      back ", bay_back, " (mains only), front ", bay_w,
         " (low voltage, clear end to end)"));
echo(str("inlet     BACK wall, x ", plug_x, ", z ", plug_z,
         "; reaches ", plug_reach, " inside a ", bay_back, " bay"));
echo(str("shield    ", sh_x1 - sh_x0 + 2*sh_wall, " x ",
         sh_y1 - sh_y0 + sh_wall, " x ", sh_z1 - floor_t + sh_wall,
         "; slot ", sh_notch_w, " x ", sh_notch_h,
         " open to the floor; gap to the supply ", psu_y0 - (sh_y1 + sh_wall)));
echo(str("DC-DC     cutout ", mod_cut_w, " x ", mod_cut_h,
         " in a ", mod_panel_t, " panel; boss ", mod_boss,
         "; clear bay behind it ", bay_w + mod_boss - mod_depth));
echo(str("lid screws ", len(lid_screws), " x M3"));
