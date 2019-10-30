# Auto-generated program tcl file

set part [lindex $argv 0]
set bitstream [lindex $argv 1]

puts "FuseSoC Xilinx FPGA Programming Tool"
puts "===================================="
puts ""
puts "INFO: Programming part $part with bitstream $bitstream"

# Connect to Xilinx Hardware Server
open_hw
connect_hw_server

# Find the first target and device that contains a FPGA $part.
set hw_device_found 0
foreach { hw_target } [get_hw_targets] {
    puts "INFO: Trying to use hardware target $hw_target"

    current_hw_target $hw_target

    # Open hardware target
    # The Vivado hardware server isn't always able to reliably open a target.
    # Try three times before giving up.
    set hw_target_opened 0
    for {set open_hw_target_try 1} {$open_hw_target_try <= 3} {incr open_hw_target_try} {
        if {[catch {open_hw_target} res_open_hw_target] == 0} {
            set hw_target_opened 1
            break
        }
    }
    if { $hw_target_opened == 0 } {
        puts "WARNING: Unable to open hardware target $hw_target after " \
            "$open_hw_target_try tries. Skipping."
        continue
    }
    puts "INFO: Opened hardware target $hw_target on try $open_hw_target_try."

    # Iterate through all devices and find one which contains $part
    foreach { hw_device } [get_hw_devices] {
        if { [string first [get_property PART $hw_device] $part] == 0 } {
            puts "INFO: Found $part as part of $hw_device."
            current_hw_device $hw_device
            set hw_device_found 1
            break
        }
    }

    if { $hw_device_found == 1 } {
        break
    } else {
        # Close currently tried device, and try with next one.
        puts "INFO: Part not found as part of $hw_target. Trying next device."
        close_hw_target
    }
}
if { $hw_device_found == 0 } {
    puts "ERROR: None of the hardware targets included a $part FPGA part. \
        Check cables and ensure that jumpers are correct for JTAG programming."
    exit 1
}
puts "INFO: Programming bitstream to device $hw_device on target $hw_target."

# Do the programming
current_hw_device $hw_device
set_property PROGRAM.FILE $bitstream [current_hw_device]
program_hw_devices [current_hw_device]

# Disconnect from Xilinx Hardware Server
close_hw_target
disconnect_hw_server

puts ""
puts "INFO: SUCCESS! FPGA $part successfully programmed with bitstream $bitstream."
