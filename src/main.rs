use std::{fs, path::PathBuf};
use clap::Parser;
use anyhow::{Result, anyhow};
use byteorder::{BigEndian, ReadBytesExt};
use std::io::{Cursor, Read};

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the .rsrc file to extract version from
    rsrc_file: PathBuf,
}

#[repr(u32)]
#[derive(Debug, Clone, Copy)]
pub enum Stage {
    Develop = 0,
    Alpha,
    Beta,
    Release,
}

#[derive(Debug)]
pub struct VersionInfo {
    pub version: u32,
    pub subversion: u32,
    pub bugversion: u32,
    pub stage: Stage,
    pub build: u32,
}

fn extract_pf_version(encoded: u32) -> VersionInfo {
    const PF_VERS_BUILD_BITS: u32 = 0x1ff;
    const PF_VERS_BUILD_SHIFT: u32 = 0;
    const PF_VERS_STAGE_BITS: u32 = 0x3;
    const PF_VERS_STAGE_SHIFT: u32 = 9;
    const PF_VERS_BUGFIX_BITS: u32 = 0xf;
    const PF_VERS_BUGFIX_SHIFT: u32 = 11;
    const PF_VERS_SUBVERS_BITS: u32 = 0xf;
    const PF_VERS_SUBVERS_SHIFT: u32 = 15;
    const PF_VERS_VERS_BITS: u32 = 0x7;
    const PF_VERS_VERS_SHIFT: u32 = 19;
    const PF_VERS_VERS_HIGH_BITS: u32 = 0xf;
    const PF_VERS_VERS_HIGH_SHIFT: u32 = 26;
    const PF_VERS_VERS_LOW_SHIFT: u32 = 3;

    let build = (encoded >> PF_VERS_BUILD_SHIFT) & PF_VERS_BUILD_BITS;
    let stage_num = (encoded >> PF_VERS_STAGE_SHIFT) & PF_VERS_STAGE_BITS;
    let bugversion = (encoded >> PF_VERS_BUGFIX_SHIFT) & PF_VERS_BUGFIX_BITS;
    let subversion = (encoded >> PF_VERS_SUBVERS_SHIFT) & PF_VERS_SUBVERS_BITS;
    
    let version_low = (encoded >> PF_VERS_VERS_SHIFT) & PF_VERS_VERS_BITS;
    let version_high = (encoded >> PF_VERS_VERS_HIGH_SHIFT) & PF_VERS_VERS_HIGH_BITS;
    let version = (version_high << PF_VERS_VERS_LOW_SHIFT) | version_low;

    let stage = match stage_num {
        0 => Stage::Develop,
        1 => Stage::Alpha,
        2 => Stage::Beta,
        3 => Stage::Release,
        _ => Stage::Develop, // default fallback
    };

    VersionInfo {
        version,
        subversion,
        bugversion,
        stage,
        build,
    }
}

fn parse_rsrc_file(data: &[u8]) -> Result<Option<u32>> {
    // Check if this is a Mac resource fork (starts with data_offset, map_offset)
    if data.len() >= 16 {
        let data_offset = u32::from_be_bytes([data[0], data[1], data[2], data[3]]);
        let map_offset = u32::from_be_bytes([data[4], data[5], data[6], data[7]]);
        
        // If this looks like a resource fork (reasonable offsets), try that format
        // But make sure there's enough space for the map header and some data
        if data_offset < data.len() as u32 && map_offset < data.len() as u32 && 
           data_offset > 0 && map_offset > data_offset && 
           map_offset + 32 < data.len() as u32 && // Need at least 32 bytes for map header
           map_offset - data_offset > 400 { // Need reasonable gap between data and map
            return parse_mac_resource_fork(data);
        }
    }
    
    // Otherwise, try parsing as 8BIM format (Photoshop plugin)
    parse_8bim_format(data)
}

fn parse_mac_resource_fork(data: &[u8]) -> Result<Option<u32>> {
    let mut cursor = Cursor::new(data);
    
    // Parse resource fork header
    let data_offset = cursor.read_u32::<BigEndian>()? as u64;
    let map_offset = cursor.read_u32::<BigEndian>()? as u64;
    let _data_length = cursor.read_u32::<BigEndian>()?;
    let _map_length = cursor.read_u32::<BigEndian>()?;
    
    println!("Mac resource fork - data_offset: {}, map_offset: {}", data_offset, map_offset);
    
    // Check if we have enough data for the map
    if map_offset + 16 >= data.len() as u64 {
        println!("Not enough data for map header");
        return Ok(None);
    }
    
    // Jump to the resource map
    cursor.set_position(map_offset);
    
    // Skip map header (16 bytes duplicate of file header)
    cursor.set_position(map_offset + 16);
    
    // Check if we have enough data for the next fields
    if cursor.position() + 10 >= data.len() as u64 {
        println!("Not enough data for map fields");
        return Ok(None);
    }
    
    // Skip next handle, next file, file ref
    cursor.set_position(map_offset + 16 + 4 + 4 + 2);
    
    // Read type list offset and name list offset
    let type_list_offset = cursor.read_u16::<BigEndian>()? as u64;
    let _name_list_offset = cursor.read_u16::<BigEndian>()? as u64;
    
    println!("Type list offset: {}, name list offset: {}", type_list_offset, _name_list_offset);
    
    // Check if we have enough data for the type list
    let type_list_pos = map_offset + type_list_offset;
    if type_list_pos + 2 >= data.len() as u64 {
        println!("Not enough data for type list");
        return Ok(None);
    }
    
    // Move to type list
    cursor.set_position(type_list_pos);
    
    // Read number of types
    let num_types = cursor.read_u16::<BigEndian>()? + 1;
    println!("Number of types: {}", num_types);
    
    // Look for PiPL resource type
    for i in 0..num_types {
        if cursor.position() + 8 >= data.len() as u64 {
            println!("Not enough data for type entry {}", i);
            break;
        }
        
        let type_code = cursor.read_u32::<BigEndian>()?;
        let num_resources = cursor.read_u16::<BigEndian>()? + 1;
        let resource_list_offset = cursor.read_u16::<BigEndian>()? as u64;
        
        println!("Type {}: code=0x{:08X}, resources={}, offset={}", i, type_code, num_resources, resource_list_offset);
        
        // Check if this is PiPL type (0x5069504C = "PiPL" in big endian)
        if type_code == 0x5069504C {
            println!("Found PiPL type!");
            // Save current position
            let current_pos = cursor.position();
            
            // Jump to resource list
            let resource_list_pos = map_offset + type_list_offset + resource_list_offset;
            if resource_list_pos >= data.len() as u64 {
                println!("Resource list position out of bounds");
                cursor.set_position(current_pos);
                continue;
            }
            
            cursor.set_position(resource_list_pos);
            
            // Read first resource (assuming ID 16000)
            for j in 0..num_resources {
                if cursor.position() + 12 >= data.len() as u64 {
                    println!("Not enough data for resource entry {}", j);
                    break;
                }
                
                let _resource_id = cursor.read_i16::<BigEndian>()?;
                let _name_offset = cursor.read_u16::<BigEndian>()?;
                let attributes_and_offset = cursor.read_u32::<BigEndian>()?;
                let _handle = cursor.read_u32::<BigEndian>()?;
                
                // Extract resource data offset
                let resource_data_offset = (attributes_and_offset & 0x00FFFFFF) as u64;
                let resource_pos = data_offset + resource_data_offset;
                
                println!("Resource {}: id={}, offset={}, pos={}", j, _resource_id, resource_data_offset, resource_pos);
                
                // Check if resource position is valid
                if resource_pos + 4 >= data.len() as u64 {
                    println!("Resource data position out of bounds");
                    continue;
                }
                
                // Jump to resource data
                cursor.set_position(resource_pos);
                
                // Read resource data length
                let resource_length = cursor.read_u32::<BigEndian>()? as usize;
                
                if resource_pos + 4 + resource_length as u64 > data.len() as u64 {
                    println!("Resource data length out of bounds: {}", resource_length);
                    continue;
                }
                
                // Read the PiPL data
                let mut pipl_data = vec![0u8; resource_length];
                cursor.read_exact(&mut pipl_data)?;
                
                // Parse PiPL properties to find ae_effect_version
                if let Some(version) = parse_pipl_data(&pipl_data)? {
                    return Ok(Some(version));
                }
            }
            
            // Restore position to continue looking
            cursor.set_position(current_pos);
        }
    }
    
    println!("No PiPL resources found");
    Ok(None)
}

fn parse_8bim_format(data: &[u8]) -> Result<Option<u32>> {
    let mut cursor = Cursor::new(data);
    
    // Start from the beginning and look for 8BIM chunks
    cursor.set_position(0);
    
    // Look for 8BIM chunks
    while cursor.position() < data.len() as u64 - 8 {
        // Read chunk signature
        let mut signature = [0u8; 4];
        if cursor.read_exact(&mut signature).is_err() {
            break;
        }
        
        // Check if this is an 8BIM chunk
        if &signature == b"8BIM" {
            // Read chunk key
            let mut key = [0u8; 4];
            if cursor.read_exact(&mut key).is_err() {
                break;
            }
            
            // Read chunk length (first length field)
            let length1 = cursor.read_u32::<BigEndian>()?;
            
            // Check if this is the eVER chunk (AE effect version)
            if &key == b"eVER" {
                // Read the second length field
                let _length2 = cursor.read_u32::<BigEndian>()?;
                // Read the encoded version value
                let encoded_version = cursor.read_u32::<BigEndian>()?;
                return Ok(Some(encoded_version));
            } else {
                // Skip this chunk's data
                cursor.set_position(cursor.position() + length1 as u64);
            }
        } else {
            // Skip this chunk
            cursor.set_position(cursor.position() - 4); // Go back to before signature
            cursor.set_position(cursor.position() + 1); // Skip one byte and try again
        }
    }
    
    Ok(None)
}

fn parse_pipl_data(data: &[u8]) -> Result<Option<u32>> {
    let mut cursor = Cursor::new(data);
    
    // Skip version (4 bytes) and read number of properties
    cursor.set_position(4);
    let num_properties = cursor.read_u32::<BigEndian>()?;
    
    // Parse each property
    for _ in 0..num_properties {
        // Read property signature (4 bytes)
        let mut signature = [0u8; 4];
        cursor.read_exact(&mut signature)?;
        
        // Read property key (4 bytes)
        let mut key = [0u8; 4];
        cursor.read_exact(&mut key)?;
        
        // Skip padding (4 bytes)
        cursor.set_position(cursor.position() + 4);
        
        // Read property length
        let length = cursor.read_u32::<BigEndian>()?;
        
        // Check if this is the AE_Effect_Version property ("eVER")
        if &key == b"eVER" {
            // Read the encoded version value
            let encoded_version = cursor.read_u32::<BigEndian>()?;
            return Ok(Some(encoded_version));
        } else {
            // Skip this property's data
            cursor.set_position(cursor.position() + length as u64);
            
            // Skip padding to align to 4-byte boundary on macOS
            if cfg!(target_os = "macos") {
                let padding = if length % 4 != 0 { 4 - (length % 4) } else { 0 };
                cursor.set_position(cursor.position() + padding as u64);
            }
        }
    }
    
    Ok(None)
}

fn main() -> Result<()> {
    let args = Args::parse();
    
    // Read the .rsrc file
    let data = fs::read(&args.rsrc_file)
        .map_err(|e| anyhow!("Failed to read file '{}': {}", args.rsrc_file.display(), e))?;
    
    // Parse the resource file to find the encoded version
    let encoded_version = parse_rsrc_file(&data)?
        .ok_or_else(|| anyhow!("AE effect version not found in file"))?;
    
    // Decode the version
    let version_info = extract_pf_version(encoded_version);
    
    // Print the results
    println!("Raw encoded version: 0x{:08X}", encoded_version);
    println!("Decoded version information:");
    println!("  Version: {}", version_info.version);
    println!("  Subversion: {}", version_info.subversion);
    println!("  Bug version: {}", version_info.bugversion);
    println!("  Stage: {:?}", version_info.stage);
    println!("  Build: {}", version_info.build);
    println!("  Full version: {}.{}.{} {:?} (Build {})",
        version_info.version, 
        version_info.subversion, 
        version_info.bugversion, 
        version_info.stage,
        version_info.build
    );
    
    Ok(())
}
