/**
 *Submitted for verification at Etherscan.io on 2023-04-16
*/

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract TranscriptContract {

    address public owner;

    enum Role { 
        STUDENT,
        PROFESSOR,
        ADMINISTRATOR
    }

    struct Person{
        address owner; 
        Role role;
    }

    struct Transcript {
        address owner;
        bytes32 hash;
        uint256 timestamp; 
    }
        
    mapping (bytes32 => Transcript) transcripts;
    mapping (address => Person) persons;


    constructor() {
        owner = msg.sender;
        persons[owner] = Person(owner, Role.ADMINISTRATOR);
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this operation.");
        _;
    }

    modifier noRoleYet(address adr) {
        require(persons[adr].owner == address(0), "this address already has a role");
        _;
    }

    modifier HasARole(address adr) {
        require(persons[adr].owner != address(0), "this address doesn't exist");
        _;
    }

    modifier isAnAdministrator() {
        require( persons[msg.sender].role == Role.ADMINISTRATOR, "you don't have access to create transcript");
        _;
    }

    function changeOwner(address adr) public onlyOwner{
        require(owner != adr, "you're already the owner");
        owner = adr;
    }

    function addAdministrator(address adr) public onlyOwner noRoleYet(adr) {
        persons[adr] = Person(adr, Role.ADMINISTRATOR);
    } 

    function addStudent(address adr) public onlyOwner noRoleYet(adr) {
        persons[adr] = Person(adr, Role.STUDENT);
    } 

    function addProfessor(address adr) public onlyOwner noRoleYet(adr) {
        persons[adr] = Person(adr, Role.PROFESSOR);
    }    

    function updateRole(address adr, Role role) public onlyOwner HasARole(adr) {
        require(persons[adr].role != role, "this address already has this role");
        persons[adr].role = role;
    }

    function checkPerson(address adr) public view returns(address, Role){
        Person memory person = persons[adr];
        return (person.owner, person.role);
    }

    function deletePerson(address adr) public onlyOwner HasARole(adr) {
        delete persons[adr];
    }

    function verifyTranscript(bytes32 _hash) public view returns (bool){
        Transcript memory t = transcripts[_hash];
        if(t.owner == address(0)){
            return false;
        }
        return true;
    }

    function createTranscript(bytes32 _hash) public HasARole(msg.sender) isAnAdministrator  {
        require(!verifyTranscript(_hash), "this hash already exists");
        transcripts[_hash] = Transcript(msg.sender, _hash, block.timestamp);
    }
    
    function getTranscript(bytes32 _hash) public view returns (bytes32, address, uint256) {
        Transcript memory t = transcripts[_hash];
        return (t.hash, t.owner, t.timestamp);
    }

    function deleteTranscript(bytes32 _hash)  public HasARole(msg.sender) isAnAdministrator{
        require(verifyTranscript(_hash), "this hash doesn't exist");
        delete transcripts[_hash];
    }
}